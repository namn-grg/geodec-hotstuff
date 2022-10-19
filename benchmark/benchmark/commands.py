from os.path import join

from benchmark.utils import PathMaker


class CommandMaker:

    @staticmethod
    def cleanup():
        return (
            f'rm -r .db-* ; rm .*.json ; mkdir -p {PathMaker.results_path()}'
        )

    @staticmethod
    def clean_logs():
        return f'rm -r {PathMaker.logs_path()} ; mkdir -p {PathMaker.logs_path()}'

    @staticmethod
    def compile():
        return 'cargo build --quiet --release --features benchmark'

    @staticmethod
    def generate_key(filename):
        assert isinstance(filename, str)
        return f'./node keys --filename {filename}'
    
    @staticmethod
    def initalizeDelayQDisc(interface):
        return (f'sudo tc qdisc add dev {interface} parent root handle 1:0 htb default 100')
    
    @staticmethod
    def deleteDelayQDisc(interface):
        return (f'sudo tc qdisc del dev {interface} parent root')

    @staticmethod
    def getDelayCommand(n, ip, interface, delay, delay_dev):
        return (f'sudo tc class add dev {interface} parent 1:0 classid 1:{n+1} htb rate 1000kbit; sudo tc filter add dev {interface} parent 1:0 protocol ip u32 match ip dst {ip} flowid 1:{n}; sudo tc qdisc add dev {interface} parent 1:{n} handle {n*10}:0 netem delay {delay}ms {delay_dev}ms; ')

    @staticmethod
    def run_node(keys, committee, store, parameters, debug=False):
        assert isinstance(keys, str)
        assert isinstance(committee, str)
        assert isinstance(parameters, str)
        assert isinstance(debug, bool)
        v = '-vvv' if debug else '-vv'
        return (f'./node {v} run --keys {keys} --committee {committee} '
                f'--store {store} --parameters {parameters}')

    @staticmethod
    def run_client(address, size, rate, timeout, nodes=[]):
        assert isinstance(address, str)
        assert isinstance(size, int) and size > 0
        assert isinstance(rate, int) and rate >= 0
        assert isinstance(nodes, list)
        assert all(isinstance(x, str) for x in nodes)
        nodes = f'--nodes {" ".join(nodes)}' if nodes else ''
        return (f'./client --size {size} '
                f'--rate {rate} --timeout {timeout} --nodes {address} {address}')

    @staticmethod
    def kill():
        return 'tmux kill-server'

    @staticmethod
    def alias_binaries(origin):
        assert isinstance(origin, str)
        node, client = join(origin, 'node'), join(origin, 'client')
        return f'rm node ; rm client ; ln -s {node} . ; ln -s {client} .'
