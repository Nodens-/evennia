"""
Unit tests for the EvMenu system

TODO: This need expansion.

"""

import copy
from django.test import TestCase
from evennia.utils import evmenu
from evennia.utils import ansi
from mock import MagicMock


class TestEvMenu(TestCase):
    "Run the EvMenu testing."
    menutree = {}  # can also be the path to the menu tree
    startnode = "start"
    cmdset_mergetype = "Replace"
    cmdset_priority = 1
    auto_quit = True
    auto_look = True
    auto_help = True
    cmd_on_exit = "look"
    persistent = False
    startnode_input = ""
    kwargs = {}

    # this is compared against the full tree structure generated
    expected_tree = []
    # this allows for verifying that a given node returns a given text. The
    # text is compared with .startswith, so the entire text need not be matched.
    expected_node_texts = {}
    # just check the number of options from each node
    expected_node_options_count = {}
    # check the actual options
    expected_node_options = {}

    # set this to print the traversal as it happens (debugging)
    debug_output = False

    def _debug_output(self, indent, msg):
        if self.debug_output:
            print(" " * indent + msg)

    def _test_menutree(self, menu):
        """
        This is a automatic tester of the menu tree by recursively progressing through the
        structure.
        """

        def _depth_first(menu, tree, visited, indent):

            # we are in a given node here
            nodename = menu.nodename
            options = menu.test_options
            if isinstance(options, dict):
                options = (options, )

            # run validation tests for this node
            compare_text = self.expected_node_texts.get(nodename, None)
            if compare_text is not None:
                compare_text = ansi.strip_ansi(compare_text.strip())
                node_text = menu.test_nodetext
                self.assertIsNotNone(
                    bool(node_text),
                    "node: {}: node-text is None, which was not expected.".format(nodename))
                node_text = ansi.strip_ansi(node_text.strip())
                self.assertTrue(
                    node_text.startswith(compare_text),
                    "\nnode \"{}\':\nOutput:\n{}\n\nExpected (startswith):\n{}".format(
                        nodename, node_text, compare_text))
            compare_options_count = self.expected_node_options_count.get(nodename, None)
            if compare_options_count is not None:
                self.assertEqual(
                    len(options), compare_options_count,
                    "Not the right number of options returned from node {}.".format(nodename))
            compare_options = self.expected_node_options.get(nodename, None)
            if compare_options:
                self.assertEqual(
                    options, compare_options,
                    "Options returned from node {} does not match.".format(nodename))

            self._debug_output(indent, "*{}".format(nodename))
            subtree = []

            if not options:
                # an end node
                if nodename not in visited:
                    visited.append(nodename)
                subtree = nodename
            else:
                for inum, optdict in enumerate(options):

                    key, desc, execute, goto = optdict.get("key", ""), optdict.get("desc", None),\
                                               optdict.get("exec", None), optdict.get("goto", None)

                    # prepare the key to pass to the menu
                    if isinstance(key, (tuple, list)) and len(key) > 1:
                        key = key[0]
                    if key == "_default":
                        key = "test raw input"
                    if not key:
                        key = str(inum + 1)

                    backup_menu = copy.copy(menu)

                    # step the menu
                    menu.parse_input(key)

                    # from here on we are likely in a different node
                    nodename = menu.nodename

                    if menu.close_menu.called:
                        # this was an end node
                        self._debug_output(indent, "    .. menu exited! Back to previous node.")
                        menu = backup_menu
                        menu.close_menu = MagicMock()
                        visited.append(nodename)
                        subtree.append(nodename)
                    elif nodename not in visited:
                        visited.append(nodename)
                        subtree.append(nodename)
                        _depth_first(menu, subtree, visited, indent + 2)
                        #self._debug_output(indent, "    -> arrived at {}".format(nodename))
                    else:
                        subtree.append(nodename)
                        #self._debug_output( indent, "    -> arrived at {} (circular call)".format(nodename))
                    self._debug_output(indent, "-- {} ({}) -> {}".format(key, desc, goto))

            if subtree:
                tree.append(subtree)

        # the start node has already fired at this point
        visited_nodes = [menu.nodename]
        traversal_tree = [menu.nodename]
        _depth_first(menu, traversal_tree, visited_nodes, 1)

        self.assertGreaterEqual(len(menu._menutree), len(visited_nodes))
        self.assertEqual(traversal_tree, self.expected_tree)

    def setUp(self):
        self.menu = None
        if self.menutree:
            self.caller = MagicMock()
            self.caller.key = "Test"
            self.caller2 = MagicMock()
            self.caller2.key = "Test"
            self.caller.msg = MagicMock()
            self.caller2.msg = MagicMock()
            self.session = MagicMock()
            self.session2 = MagicMock()
            self.menu = evmenu.EvMenu(self.caller, self.menutree, startnode=self.startnode,
                                      cmdset_mergetype=self.cmdset_mergetype,
                                      cmdset_priority=self.cmdset_priority,
                                      auto_quit=self.auto_quit, auto_look=self.auto_look,
                                      auto_help=self.auto_help,
                                      cmd_on_exit=self.cmd_on_exit, persistent=False,
                                      startnode_input=self.startnode_input, session=self.session,
                                      **self.kwargs)
            # persistent version
            self.pmenu = evmenu.EvMenu(self.caller2, self.menutree, startnode=self.startnode,
                                       cmdset_mergetype=self.cmdset_mergetype,
                                       cmdset_priority=self.cmdset_priority,
                                       auto_quit=self.auto_quit, auto_look=self.auto_look,
                                       auto_help=self.auto_help,
                                       cmd_on_exit=self.cmd_on_exit, persistent=True,
                                       startnode_input=self.startnode_input, session=self.session2,
                                       **self.kwargs)

            self.menu.close_menu = MagicMock()
            self.pmenu.close_menu = MagicMock()

    def test_menu_structure(self):
        if self.menu:
            self._test_menutree(self.menu)
            self._test_menutree(self.pmenu)


class TestEvMenuExample(TestEvMenu):

    menutree = "evennia.utils.evmenu"
    startnode = "test_start_node"
    kwargs = {"testval": "val", "testval2": "val2"}
    debug_output = False

    expected_node_texts = {
        "test_view_node": "Your name is"}

    expected_tree = \
        ['test_start_node',
         ['test_set_node',
          ['test_start_node'],
          'test_look_node',
          ['test_start_node'],
          'test_view_node',
          ['test_start_node'],
          'test_dynamic_node',
          ['test_dynamic_node',
           'test_dynamic_node',
           'test_dynamic_node',
           'test_dynamic_node',
           'test_start_node'],
          'test_end_node',
          'test_displayinput_node',
          ['test_start_node']]]

    def test_kwargsave(self):
        self.assertTrue(hasattr(self.menu, "testval"))
        self.assertTrue(hasattr(self.menu, "testval2"))