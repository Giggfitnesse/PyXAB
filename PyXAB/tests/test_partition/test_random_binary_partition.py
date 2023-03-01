from PyXAB.partition.RandomBinaryPartition import RandomBinaryPartition
import pytest

def test_random_binary_partition_1():
    with pytest.raises(ValueError):
        RandomBinaryPartition()

def test_random_binary_partition_2():
    domain = [[0, 1]]
    part = RandomBinaryPartition(domain)

    for i in range(5):
        part.deepen()
        nodelist = part.get_node_list()
        for node in nodelist[-1]:
            print(node.depth, node.index, node.domain, "\\")

def test_random_binary_partition_3():
    domain = [[0, 1], [10, 50], [-5, -10]]
    part = RandomBinaryPartition(domain)

    for i in range(2):
        part.deepen()
        nodelist = part.get_node_list()
        for node in nodelist[-1]:
            print(node.depth, node.index, node.domain, "\\")