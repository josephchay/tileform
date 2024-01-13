# prototype phase

import os
import sys

import pygame
from pygame.locals import *
import json


class EventHandler:
    def __init__(self, path):
        """
        Handles all input events from the given JSON configuration file

        :param path: The path to the JSON configuration file
        """

        with open(os.path.join(path), 'r') as file:
            self.config = json.load(file)

        self.input_to_action_map = {}
        self.action_to_handler_map = {}
        self.held_keys = set()
        self.prior_keys = set()
        self.active_continuous_actions = set()

        self._map_inputs()

    def _map_inputs(self):
        for context, actions in self.config.items():
            for action_name, input_details in actions.items():
                for input_type, details in input_details.items():
                    for ord_value in details['ord']:
                        input_key = (input_type, ord_value, tuple(details['held']), tuple(details['prior']))
                        action_key = (context, action_name)
                        self.input_to_action_map[input_key] = {
                            'action': action_key,
                            'held': details['held'],
                            'prior': details['prior'],
                            'exclusive': details['exclusive'],
                            'continuous': details.get('continuous', False)
                        }

    def handle(self, context: str, action: str, handler: callable) -> None:
        """
        Registers a method to be called when the given action is triggered

        :param context: The context id
        :param action: The action name to target
        :param handler: The method to call when the action is triggered
        :return: None
        """

        action = (context, action)
        if action in [mapping['action'] for mapping in self.input_to_action_map.values()]:
            self.action_to_handler_map[action] = handler
        else:
            raise ValueError(f"Action {action} is not defined in the input configuration.")

    def dehandle(self, context: str, action: str = None) -> None:
        """
        Removes the registered method for the given action

        :param context: The context id
        :param action: The action name to target
        :return: None
        """

        action = (context, action)
        if action in self.action_to_handler_map:
            del self.action_to_handler_map[action]
        else:
            raise ValueError(f"Action {action} is not defined in the input configuration.")

    def update(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            if event.type in [KEYDOWN, MOUSEBUTTONDOWN]:
                input_type = event.key if event.type == KEYDOWN else event.button
                self.held_keys.add(input_type)

                # Toggle the state of the key/button in prior_keys
                if input_type in self.prior_keys:
                    self.prior_keys.remove(input_type)
                else:
                    self.prior_keys.add(input_type)

                self._handle_down_input(event, input_type)
            elif event.type in [KEYUP, MOUSEBUTTONUP]:
                input_type = event.key if event.type == KEYUP else event.button
                self.held_keys.discard(input_type)
                self._handle_up_input(event, input_type)

        for _, action in self.active_continuous_actions:
            self._execute_action(action)

    def _handle_down_input(self, event, input_type) -> None:
        event_type = 'key' if event.type in [KEYDOWN, KEYUP] else 'mouse'
        input_info = (event_type, input_type)

        default_action = None

        for key, action_info in self.input_to_action_map.items():
            if key[0:2] == input_info:
                if action_info['prior']:
                    if all(prior in self.prior_keys for prior in action_info['prior']) and all(held in self.held_keys for held in action_info['held']):
                        if action_info['continuous']:
                            self.active_continuous_actions.add((input_type, action_info['action']))
                        else:
                            self._execute_action(action_info['action'])
                        return  # Don't check for default action if a prior action was triggered
                else:
                    default_action = action_info

        if default_action:
            if default_action['continuous']:
                self.active_continuous_actions.add((input_type, default_action['action']))
            else:
                self._execute_action(default_action['action'])

    def _handle_up_input(self, event, input_type) -> None:
        """
        Handles input that has been released

        :param event: The pygame event
        :param input_type: The input type
        :return: None
        """

        # stop continuous actions
        actions_to_remove = {action for action in self.active_continuous_actions if action[0] == input_type}
        for action in actions_to_remove:
            self.active_continuous_actions.remove(action)

    def _execute_action(self, action):
        if action in self.action_to_handler_map:
            self.action_to_handler_map[action]()
            print(f"Action {action} triggered.")
        else:
            print(f"No method registered for action: {action}")
