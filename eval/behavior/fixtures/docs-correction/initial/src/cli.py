import argparse


def parser():
    result = argparse.ArgumentParser()
    result.add_argument('--limit', type=int, default=25, choices=range(1, 101))
    result.add_argument('--format', choices=['json', 'text'], default='json')
    return result
