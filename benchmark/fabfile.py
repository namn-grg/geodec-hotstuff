from fabric import task

from benchmark.local import LocalBench
from benchmark.logs import ParseError, LogParser
from benchmark.utils import Print
from benchmark.plot import Ploter, PlotError
from benchmark.instance import InstanceManager
from benchmark.remote import Bench, BenchError


@task
def local(ctx):
    ''' Run benchmarks on localhost '''
    bench_params = {
        'faults': 0,
        'nodes': 4,
        'rate': 1_000,
        'tx_size': 512,
        'duration': 20,
    }
    node_params = {
        'consensus': {
            'timeout_delay': 1_000,
            'sync_retry_delay': 10_000,
        },
        'mempool': {
            'gc_depth': 50,
            'sync_retry_delay': 5_000,
            'sync_retry_nodes': 3,
            'batch_size': 15_000,
            'max_batch_delay': 10
        }
    }
    try:
        ret = LocalBench(bench_params, node_params).run(debug=True).result()
        print(ret)
    except BenchError as e:
        Print.error(e)


@task
def create(ctx, nodes=2):
    ''' Create a testbed'''
    try:
        InstanceManager.make().create_instances(nodes)
    except BenchError as e:
        Print.error(e)


@task
def destroy(ctx):
    ''' Destroy the testbed '''
    try:
        InstanceManager.make().terminate_instances()
    except BenchError as e:
        Print.error(e)


@task
def start(ctx, max=2):
    ''' Start at most `max` machines per data center '''
    try:
        InstanceManager.make().start_instances(max)
    except BenchError as e:
        Print.error(e)


@task
def stop(ctx):
    ''' Stop all machines '''
    try:
        InstanceManager.make().stop_instances()
    except BenchError as e:
        Print.error(e)


@task
def info(ctx):
    ''' Display connect information about all the available machines '''
    try:
        InstanceManager.make().print_info()
    except BenchError as e:
        Print.error(e)


@task
def install(ctx):
    ''' Install the codebase on all machines '''
    try:
        Bench(ctx).install()
    except BenchError as e:
        Print.error(e)


@task
def remote(ctx):
    ''' Run benchmarks on a cluster'''
    
    bench_params = {
        'faults': 0,
        'nodes': [4],
        'rate': [20000],
        'tx_size': 512,
        'duration': 20,
        'runs': 1,
    }
    node_params = {
        'consensus': {
            'timeout_delay': 50_000,
            'sync_retry_delay': 50_000,
        },
        'mempool': {
            'gc_depth': 50,
            'sync_retry_delay': 5_000,
            'sync_retry_nodes': 3,
            'batch_size': 204800,
            'max_batch_delay': 100
        }
    }
  
    
    try:
        Bench(ctx).run(bench_params, node_params, None, debug=False)
    except BenchError as e:
        Print.error(e)

@task
def georemote(ctx):
    ''' Run benchmarks on ComputeCanada/AWS '''
    # test GeoInput  
    geoInput = {23: 20, 45: 20, 50: 1, 46: 1, 95: 1, 169: 1, 18: 1, 7: 2, 37: 1, 24: 2, 16: 1, 13: 1, 47: 2, 54: 1, 19: 2, 89: 1, 4: 1, 76: 1, 12: 2, 22: 1, 140: 1}
    
    bench_params = {
        'faults': 0,
        'nodes': [64],
        'rate': [20000],
        'tx_size': 512,
        'duration': 300,
        'runs': 5,
    }
    node_params = {
        'consensus': {
            'timeout_delay': 50_000,
            'sync_retry_delay': 50_000,
        },
        'mempool': {
            'gc_depth': 50,
            'sync_retry_delay': 5_000,
            'sync_retry_nodes': 3,
            'batch_size': 204800,
            'max_batch_delay': 100
        }
    }
  
    
    try:
        Bench(ctx).run(bench_params, node_params, geoInput, debug=False)
    except BenchError as e:
        Print.error(e)


@task
def plot(ctx):
    ''' Plot performance using the logs generated by "fab remote" '''
    plot_params = {
        'faults': [0],
        'nodes': [10, 20, 50],
        'tx_size': 32,
        'max_latency': [2_000, 5_000]
    }
    try:
        Ploter.plot(plot_params)
    except PlotError as e:
        Print.error(BenchError('Failed to plot performance', e))


@task
def kill(ctx):
    ''' Stop any HotStuff execution on all machines '''
    try:
        Bench(ctx).kill()
    except BenchError as e:
        Print.error(e)


@task
def logs(ctx):
    ''' Print a summary of the logs '''
    try:
        print(LogParser.process('./logs', faults='?').result())
    except ParseError as e:
        Print.error(BenchError('Failed to parse logs', e))
