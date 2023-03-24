import json
import typing

import openai
from back.models import ConversationMessage as Message
from back.session import session


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


def hashkey(x) -> str:
    """Hash a list of dictionaries"""
    return str(hash(json.dumps(x, sort_keys=True)))


def cache_db(f):
    def wrapper(messages: list[Message]) -> dict:
        from back.models import Prediction

        messages_dict = [m.to_openai_dict() for m in messages]

        """Cache on database Prediction table"""
        key = hashkey(messages_dict)
        prediction = session.query(Prediction).filter_by(params_hash=key).first()
        if prediction:
            return {
                "role": "assistant",
                "content": prediction.value,
            }
        else:
            response = f(messages_dict)
            message = response.choices[0].message
            prediction = Prediction(
                prompt=messages_dict[-1]["content"],  # last message is the prompt
                params_hash=key,
                modelName=response.model,
                response=response,
                params=messages_dict,
                output=message["content"],
                value=message["content"],
            )
            session.add(prediction)
            session.commit()
            return message

    return wrapper


@cache_db
def fetch_openai(messages: list[dict]) -> dict:
    # https://platform.openai.com/docs/models/gpt-4
    model = "gpt-4-0314"
    # model = "gpt-4"
    # model = "gpt-4-32k"
    # model = "gpt-4-32k-0314"
    # model = "gpt-3.5-turbo"
    result = openai.ChatCompletion.create(model=model, messages=messages)
    # result = requests.post(
    #     "https://api.openai.com/v1/chat/completions",
    #     headers={"Authorization": "Bearer " + openai.api_key},
    #     json={"model": "gpt-4", "messages": messages},
    # ).json()
    return result


class ChatGPT:
    def __init__(self, instruction=None, examples=[]):
        self.pre_history: list[Message] = []
        self.history: list[Message] = []
        self.instruction: typing.Optional[str] = instruction
        self.examples = examples

        if self.instruction:
            self.pre_history.append(
                Message(**{"role": "system", "content": self.instruction})
            )

        # Loop, 2 by 2, over the examples
        for i in range(0, len(self.examples), 2):
            self.pre_history.append(
                Message(
                    **{
                        "role": "system",
                        "name": "example_user",
                        "content": self.examples[i],
                    }
                )
            )
            self.pre_history.append(
                Message(
                    **{
                        "role": "system",
                        "name": "example_assistant",
                        "content": self.examples[i + 1],
                    }
                )
            )

    @property
    def last_message(self):
        if not self.history:
            return None
        return self.history[-1].content

    def reset(self):
        self.history = []

    def load_history(self, messages: list[Message]):
        # Check order of messages (based on createdAt)
        # Oldest first (createdAt ASC)
        messages = sorted(messages, key=lambda x: x.createdAt)
        self.history = [message for message in messages]

    def ask(self, question):
        messages = []

        for message in self.pre_history:
            messages.append(message)

        # Add history of conversation
        for message in self.history:
            messages.append(message)

        new_message = Message(**{"role": "user", "content": question})
        messages.append(new_message)
        # Add the question

        message = fetch_openai(tuple(messages))
        self.history.append(new_message)
        self.history.append(message)

        # print(message['content'])
        return message.content
