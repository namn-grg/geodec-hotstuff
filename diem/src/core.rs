use crate::committee::Committee;
use crate::crypto::Digestible;
use crate::crypto::PublicKey;
use crate::error::{DiemError, DiemResult};
use crate::leader::LeaderElection;
use crate::messages::{Block, Vote, QC};
use crate::store::Store;
use log::{debug, error, info, warn};
use serde::{Deserialize, Serialize};
use std::cmp::max;
use tokio::sync::mpsc::{Receiver, Sender};

pub type RoundNumber = u64;

#[derive(Serialize, Deserialize, Debug)]
pub enum CoreMessage {
    Block(Block),
    Vote(Vote),
}

pub struct Core<L: LeaderElection> {
    name: PublicKey,
    round: RoundNumber,
    last_voted_round: RoundNumber,
    preferred_round: RoundNumber,
    highest_qc: (QC, RoundNumber),
    committee: Committee,
    store: Store,
    leader_election: L,
    sender: Sender<CoreMessage>,
    receiver: Receiver<CoreMessage>,
    commit_channel: Sender<Block>,
}

impl<L: LeaderElection> Core<L> {
    pub fn new(
        name: PublicKey,
        store: Store,
        committee: Committee,
        leader_election: L,
        sender: Sender<CoreMessage>,
        receiver: Receiver<CoreMessage>,
        commit_channel: Sender<Block>,
    ) -> Self {
        // TODO: add genesis to the store?
        Self {
            name,
            round: 3,
            last_voted_round: 2,
            preferred_round: 1,
            highest_qc: (QC::genesis().pop().unwrap(), 1),
            committee,
            store,
            leader_election,
            sender,
            receiver,
            commit_channel,
        }
    }

    async fn store_block(&mut self, block: &Block) -> DiemResult<()> {
        let key = block.digest().to_vec();
        let value = bincode::serialize(block).expect("Failed to serialize valid block");
        self.store.write(key, value).await.map_err(DiemError::from)
    }

    async fn get_previous_block(&mut self, block: &Block) -> DiemResult<Block> {
        // TODO: If we don't ask for the block, it may never come.
        // Also we do not want to block this thread until we get our block.
        let bytes = self.store.notify_read(block.qc.hash.to_vec()).await?;
        bincode::deserialize(&bytes).map_err(|e| DiemError::StoreError(e.to_string()))
    }

    async fn handle_propose(&mut self, block: Block) -> DiemResult<()> {
        // Ignore old messages.
        if block.round < self.round {
            return Ok(());
        }

        // Check the block is well-formed and created by the right leader.
        block.check(&self.committee)?;
        ensure!(
            block.author == self.leader_election.get_leader(block.round),
            DiemError::UnexpectedMessage(Box::new(CoreMessage::Block(block)))
        );

        // Vote for this block if we can. The ancestors of the incoming block
        // are note as follows: B0 <- |QC0; B1| <- |QC1; B2| <- |QC2; Block|
        let b2 = self.get_previous_block(&block).await?;
        let safety_rule_1 = b2.round >= self.preferred_round;
        let safety_rule_2 = block.round > self.last_voted_round;
        if !(safety_rule_1 && safety_rule_2) {
            debug!("Cannot vote on {:?}", block);
            return Ok(());
        }
        debug!("Voting for block {:?}", block);
        let vote = Vote::new(&block, self.name)?;
        if let Err(e) = self.sender.send(CoreMessage::Vote(vote)).await {
            panic!("Core failed to send vote to the network: {}", e);
        }

        // Update state.
        self.store_block(&block).await?;
        let b1 = self.get_previous_block(&b2).await?;
        self.preferred_round = max(self.preferred_round, b1.round);
        self.last_voted_round = block.round;
        let (_, hightest_qc_round) = self.highest_qc;
        if b2.round > hightest_qc_round {
            self.highest_qc = (block.qc, b2.round);
        }
        if b2.round + 1 > self.round {
            self.round = b2.round + 1;
            info!("Moved to round {}", self.round);
        }

        // Try to commit ancestors.
        let b0 = self.get_previous_block(&b1).await?;
        let mut commit = b0.round + 1 == b1.round;
        commit &= b1.round + 1 == b2.round;
        commit &= b2.round + 1 == block.round;
        if commit {
            info!("Committed {:?}", b0);
            if let Err(e) = self.commit_channel.send(b0).await {
                warn!("Failed to send block through the commit channel: {}", e);
            }
        }
        Ok(())
    }

    async fn handle_vote(&self, _vote: Vote) -> DiemResult<()> {
        // TODO
        Ok(())
    }

    pub async fn run(&mut self) {
        while let Some(message) = self.receiver.recv().await {
            debug!("Received message: {:?}", message);
            let result = match message {
                CoreMessage::Block(block) => self.handle_propose(block).await,
                CoreMessage::Vote(vote) => self.handle_vote(vote).await,
            };
            match result {
                Ok(()) => debug!("Message successfully processed."),
                Err(e) => match e {
                    DiemError::StoreError(e) => error!("{}", e),
                    _ => warn!("{}", e),
                },
            }
        }
    }
}
