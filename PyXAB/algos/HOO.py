# -*- coding: utf-8 -*-
"""Implementation of T-HOO, the truncated version of the HOO algorithm. (Bubeck et al, 2011)
    The original HOO algorithm suffers from large space complexity.
"""
# Author: Wenjie Li <li3549@purdue.edu>
# License: MIT

import math
import numpy as np
from PyXAB.algos.Algo import Algorithm
from PyXAB.partition.Node import P_node
import pdb


class HOO_node(P_node):
    """
    Implementation of the HOO_node
    """

    def __init__(self, depth, index, parent, domain):
        """
        Initialization of the HOO node

        Parameters
        ----------
        depth: int
            depth of the node
        index: int
            index of the node
        parent:
            parent node of the current node
        domain: list(list)
            domain that this node represents
        """
        super(HOO_node, self).__init__(depth, index, parent, domain)

        self.b_value = np.inf
        self.u_value = np.inf
        self.visited_times = 0
        self.rewards = []
        self.mean_reward = 0

    def update_reward(self, reward):
        """
        The function to update the reward list of the node

        Parameters
        ----------
        reward: float
            the reward for evaluating the node

        Returns
        -------

        """
        self.visited_times += 1
        self.rewards.append(reward)
        self.mean_reward = np.sum(np.array(self.rewards)) / self.visited_times

    def compute_u_value(self, nu, rho, rounds):
        """
        The function to compute the u_{h,i} value of the node

        Parameters
        ----------
        nu: float
            parameter nu in the HOO algorithm
        rho: float
            parameter rho in the HOO algorithm
        rounds: int
            the number of rounds in the HOO algorithm

        Returns
        -------

        """
        if self.visited_times == 0:
            self.b_value = np.inf
        else:
            self.mean_reward = np.sum(np.array(self.rewards)) / self.visited_times
            UCB = math.sqrt(2 * math.log(rounds) / self.visited_times)
            self.u_value = self.mean_reward + UCB + nu * (rho ** self.depth)

    def update_b_value(self, b_value):
        """
        The function to update the b_{h,i} value of the node

        Parameters
        ----------
        b_value: float
            The new b_{h,i} value to be updated

        Returns
        -------

        """
        self.b_value = b_value

    def get_visited_times(self):
        """
        The function to get the number of visited times of the node

        Returns
        -------

        """
        return self.visited_times

    def get_b_value(self):
        """
        The function to get the b_{h,i} value of the node

        Returns
        -------

        """
        return self.b_value

    def get_u_value(self):
        """
        The function to get the u_{h,i} value of the node

        Returns
        -------

        """
        return self.u_value

    def get_mean_reward(self):
        """
        The function to get the mean reward of the node

        Returns
        -------

        """
        return self.mean_reward


class T_HOO(Algorithm):
    """
    Implementation of the T_HOO algorithm
    """

    def __init__(self, nu=1, rho=0.5, rounds=1000, domain=None, partition=None):
        """
        Initialization of the T_HOO algorithm

        Parameters
        ----------
        nu: float
            parameter nu of the T_HOO algorithm
        rho: float
            parameter rho of the T_HOO algorithm
        rounds: int
            total number of rounds
        domain: list(list)
            The domain of the objective to be optimized
        partition:
            The partition choice of the algorithm
        """
        super(T_HOO, self).__init__()
        if domain is None:
            raise ValueError("Parameter space is not given.")
        if partition is None:
            raise ValueError("Partition of the parameter space is not given.")
        self.partition = partition(domain=domain, node=HOO_node)

        self.iteration = 0
        self.nu = nu
        self.rho = rho
        self.rounds = rounds

        self.expand(self.partition.get_root())

    def optTraverse(self):
        """
        The function to traverse the exploration tree to find the best path and the best node to pull at this moment.

        Returns
        -------
        curr_node: Node
            The last node selected by the algorithm
        path: List of Node
            The best path to traverse the partition selected by the algorithm
        """

        curr_node = self.partition.get_root()
        path = [curr_node]

        while curr_node.get_children() is not None:
            children = curr_node.get_children()
            maxchild = children[0]
            for child in children[1:]:
                if child.get_b_value() >= maxchild.get_b_value():
                    maxchild = child

            curr_node = maxchild
            path.append(maxchild)

        return curr_node, path

    def updateRewardTree(self, path, reward):
        """
        The function to update the reward of each node in the path

        Parameters
        ----------
        path: list
            the path to find the best node
        reward: float
            the reward to update

        Returns
        -------

        """
        for node in path:
            # Update the visited times and the average reward of the pulled node
            node.update_reward(reward)

        self.iteration += 1

    def updateUvalueTree(self):
        """
        The function to update the u_{h,i} value in the whole tree

        Returns
        -------

        """
        node_list = self.partition.get_node_list()
        for layer in node_list:
            for node in layer:
                node.compute_u_value(nu=self.nu, rho=self.rho, rounds=self.rounds)

    def updateBackwardTree(self):
        """
        The function to update all the b_{h,i} value backwards in the tree

        Returns
        -------

        """
        nodes = self.partition.get_node_list()

        for i in range(1, self.partition.get_depth() + 1):
            layer = nodes[-i]
            for node in layer:
                # If no children or if children not visitied, use its own U value
                children = node.get_children()
                if children is None:
                    node.update_b_value(node.get_u_value())
                else:
                    tempB = -np.inf
                    for child in node.get_children():
                        tempB = np.maximum(tempB, child.get_b_value())
                    node.update_b_value(np.minimum(node.get_u_value(), tempB))

    def expand(self, parent):
        """
        The function to expand the tree after pulling the parent node

        Parameters
        ----------
        parent:
            The parent node to be expanded

        Returns
        -------

        """
        if parent.get_depth() >= self.partition.get_depth():
            self.partition.make_children(parent=parent, newlayer=True)
        else:
            self.partition.make_children(parent=parent, newlayer=False)

    def updateAllTree(self, path, reward):
        """
        The function to update everything in the tree

        Parameters
        ----------
        path: list
            the path from the root to the chosen node
        reward: float
            the reward to update

        Returns
        -------

        """
        self.updateRewardTree(path, reward)
        self.updateUvalueTree()
        # Truncate or not
        if path[-1].depth <= np.ceil(
            (np.log(self.rounds) / 2 - np.log(1 / self.nu)) / np.log(1 / self.rho)
        ):
            self.expand(path[-1])
        self.updateBackwardTree()

    def pull(self, time):
        """
        The pull function of T_HOO that returns a point in every round

        Parameters
        ----------
        time: int
             time stamp parameter

        Returns
        -------
        point: list
            the point to be evaluated
        """
        curr_node, self.path = self.optTraverse()
        return curr_node.get_cpoint()

    def receive_reward(self, time, reward):
        """
        The receive_reward function of T_HOO to obtain the reward and update the Statistics

        Parameters
        ----------
        time: int
            time stamp parameter
        reward: float
            the reward of the evaluation

        Returns
        -------

        """
        self.updateAllTree(self.path, reward)

    def get_last_point(self):
        """
        The function to get the last point of HOO

        Returns
        -------
        chosen_point: list
            The point chosen by the algorithm
        """

        return self.pull(0)