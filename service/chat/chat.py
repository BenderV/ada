import json

import diskcache
import openai
import requests

cache = diskcache.Cache(".cache")


def parse_chat_template(filename):
    with open(filename) as f:
        string = f.read()

    # split the string by "\n## " to get a list of speaker and message pairs
    pairs = string.split("## ")[1:]

    # split each element of the resulting list by "\n" to separate the speaker and message
    pairs = [pair.split("\n", 1) for pair in pairs]

    # create a list of tuples
    messages = [(pair[0], pair[1].strip()) for pair in pairs]

    instruction = None
    examples = []

    for message in messages:
        # If first message role is a system message, extract the example
        if message[0] == "system":
            instruction = message[1]
        else:
            examples.append(message[1])
    return instruction, examples


def hashkey(x):
    return hash(json.dumps(x))


def fetch_openai(messages):
    # check if the result is in the cache
    if hashkey(messages) in cache:
        return cache[hashkey(messages)]

    result = openai.ChatCompletion.create(model="gpt-4-0314", messages=messages)
    # result = requests.post(
    #     "https://api.openai.com/v1/chat/completions",
    #     headers={"Authorization": "Bearer " + openai.api_key},
    #     json={"model": "gpt-4", "messages": messages},
    # ).json()
    # store the result in the cache
    cache[hashkey(messages)] = result
    return result


class ChatGPT:
    def __init__(self, instruction=None, examples=[]):
        self.pre_history = []
        self.history = []
        self.instruction = instruction
        self.examples = examples

        if self.instruction:
            self.pre_history.append({"role": "system", "content": self.instruction})

        # Loop, 2 by 2, over the examples
        for i in range(0, len(self.examples), 2):
            self.pre_history.append(
                {"role": "system", "name": "example_user", "content": self.examples[i]}
            )
            self.pre_history.append(
                {
                    "role": "system",
                    "name": "example_assistant",
                    "content": self.examples[i + 1],
                }
            )

    @property
    def last_message(self):
        if not self.history:
            return None
        return self.history[-1]["content"]

    def reset(self):
        self.history = []

    def ask(self, question):
        messages = []

        for message in self.pre_history:
            messages.append(message)

        # Add history of conversation
        for message in self.history:
            messages.append(message)

        new_message = {"role": "user", "content": question}
        messages.append(new_message)
        # Add the question
        res = fetch_openai(tuple(messages))
        message = res.choices[0].message
        self.history.append(new_message)
        self.history.append(message)

        # print(message['content'])
        return message["content"]
