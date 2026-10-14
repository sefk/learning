"""Narration for each scene, split into beats.

Each beat becomes one audio clip; scenes play one beat's animations while its
clip plays, then wait out whatever audio remains.
"""

SLUG = "thinking-mode"  # output: thinking-mode-<voice>.mp4
CUE_VOICE = "brian"  # the voice the scenes' mid-beat cues were timed against
SCENES = {  # scene file -> scenes in it, in play order
    "scenes_a": ["Intro", "JustTokens", "SerialDepth"],
    "scenes_b": ["Training", "Dial", "Closing"],
}
CHAPTERS = {  # scene -> chapter title in the mp4
    "Intro": "Same model, thinking on or off",
    "JustTokens": "It's all one string of tokens",
    "SerialDepth": "Why thinking helps: serial depth",
    "Training": "Teaching a model to use its scratchpad",
    "Dial": "Thinking as a dial",
    "Closing": "Is the trace what the model really does?",
}

NARRATION = {
    "Intro": [
        "If you've used a reasoning model, you've watched it do this. You ask a "
        "question, and before it answers, it thinks. Sometimes for a few "
        "seconds. Sometimes for minutes.",
        "And you may have noticed something odd. Turning thinking on or off "
        "doesn't load a different model. Same weights. Same architecture. Same "
        "file on disk. The only thing that changes is that it writes more "
        "before it answers.",
        "So how can writing more make a model smarter? To answer that, we need "
        "three ideas. What thinking actually is, mechanically. Why extra tokens "
        "buy extra capability. And how a model learns to use them well.",
    ],
    "JustTokens": [
        "Let's start with the mechanics. Under the hood, every chat is one long "
        "string of tokens. A chat template wraps your message in special "
        "markers, and then hands the model an opening for its reply.",
        "A reasoning model has been trained so that its reply starts with a "
        "think tag. It writes its reasoning token by token, exactly the way it "
        "writes anything else. Then it closes the tag, and writes the answer.",
        "There's no separate reasoning engine here. The server just watches for "
        "those tags, and routes everything between them into a different field. "
        "That's why a streaming API hands you reasoning content separately from "
        "content.",
        "And it explains a trick you may have used yourself. If you prefill the "
        "assistant's reply with an empty think block, open tag, close tag, then "
        "from the model's point of view, the thinking is already over. The most "
        "likely next tokens are the answer.",
        "In fact, hybrid models like Qwen 3 are trained on exactly this. Their "
        "non-thinking mode is literally an empty think block. Thinking is a "
        "convention the model learned, not a switch in the hardware.",
    ],
    "SerialDepth": [
        "So why does it help? Here's the key picture. Think of each token "
        "position as a column: a stack of layers. Information flows up through "
        "the layers, and attention lets each layer look back at earlier "
        "positions.",
        "The crucial thing is that the stack has a fixed height. A model with, "
        "say, sixty-four layers gets sixty-four layers of computation to "
        "produce each token. No more. Whether the question is two plus two, or "
        "a hard proof.",
        "If the model has to answer immediately, all of the work has to happen "
        "inside that one trip up the stack. For many problems, that just isn't "
        "enough sequential steps.",
        "But watch what happens when the model writes a token. That token, the "
        "output from the top of the stack, becomes the input at the bottom of "
        "the next column. The result of one full pass gets fed back in, and the "
        "next pass can build on it.",
        "So a thousand thinking tokens don't just mean a thousand times more "
        "arithmetic. They mean the computation can be a thousand passes deep, "
        "in series. The written tokens are a scratchpad: working memory that "
        "carries forward from one pass to the next.",
        "It's the difference between multiplying thirty-seven by forty-six in "
        "your head, and doing it on paper. Your brain doesn't get any better "
        "with the paper. You just get to write down intermediate results, and "
        "come back to them.",
        "There's theory behind this, too. A transformer that answers in a "
        "single step is limited to what a fixed-depth circuit can compute. Let "
        "it generate a chain of thought, and the class of problems it can solve "
        "grows with the length of that chain.",
    ],
    "Training": [
        "That explains why thinking can help. But a model doesn't automatically "
        "use its scratchpad well. People noticed early on that just prompting "
        "with, let's think step by step, improved answers, because pretraining "
        "data is full of worked examples. Modern reasoning models go much "
        "further, with reinforcement learning.",
        "The recipe goes roughly like this. Take a problem whose answer can be "
        "checked automatically: a math problem with a known answer, or code "
        "with unit tests. Have the model attempt it, not once, but many times. "
        "Say, eight.",
        "Each attempt is a long chain of thinking, followed by an answer. A "
        "grader checks only the final answers. Some are right, some are wrong. "
        "Nobody grades the reasoning itself.",
        "Then compare each attempt to the group's average. Attempts that did "
        "better than average get all their tokens made more likely. Attempts "
        "that did worse get their tokens made less likely. Every token in the "
        "chain shares the credit, or the blame. Now repeat that over many "
        "thousands of problems.",
        "What's remarkable is what emerges. Nobody tells the model to think "
        "longer, but over training its responses get steadily longer, because "
        "longer chains win more often. And behaviors show up that nobody wrote "
        "down: checking its own work, trying another approach, and writing "
        "things like, wait, that's not right.",
        "So that 'wait' you've seen in reasoning traces isn't a scripted "
        "affectation. It was reinforced, because statistically, catching and "
        "fixing mistakes led to more right answers.",
        "The smaller models you run locally usually get much of this second "
        "hand. They're fine-tuned on reasoning traces from larger models, a "
        "kind of distillation, and then often given reinforcement learning of "
        "their own.",
    ],
    "Dial": [
        "Once you see thinking as computation, it becomes a dial. Plot accuracy "
        "against the number of thinking tokens, on a log scale, and for many "
        "hard tasks you get a fairly steady climb. Each doubling of thinking "
        "buys another increment of accuracy.",
        "This is what people mean by test-time compute. Instead of only scaling "
        "up the model, you can scale up how long it thinks about each problem.",
        "Effort settings and thinking budgets are how you turn that dial. Some "
        "models are trained to read a budget and pace themselves. The blunt "
        "version is simpler: when the budget runs out, the server inserts the "
        "closing think tag, and forces the answer.",
        "You can push the other way, too. One research group found that when a "
        "model tried to stop thinking, appending the word, wait, made it keep "
        "going, and often fix its answer.",
        "But the dial has a price. Every thinking token is a full forward pass: "
        "latency, and on an API, money. You've seen this on your own machine. "
        "A few hundred thinking tokens on every multiple-choice question turns "
        "a benchmark run into an overnight job. And on easy questions, that "
        "spend buys nothing.",
    ],
    "Closing": [
        "One last question. When you read a thinking trace, are you seeing what "
        "the model is really doing?",
        "Partly. The tokens are genuinely load-bearing: they're inputs to "
        "everything that comes after, so the answer really does depend on them. "
        "But the trace is still text sampled from the model, shaped by training "
        "to reach right answers, not to be an honest log. Researchers have "
        "caught models using hints they were given, without ever mentioning "
        "them in their reasoning.",
        "That's one reason frontier APIs often show you a summary of the "
        "thinking instead of the raw trace, while the models on your own "
        "machine show you everything.",
        "So here's the whole picture. Same network, same weights. Thinking is "
        "just tokens, between tags the model learned to write. Those tokens "
        "matter because each one feeds a full pass back into the next, turning "
        "a fixed-depth network into a deep, serial computation. And "
        "reinforcement learning, rewarding only right answers, teaches the "
        "model how to spend that computation well.",
        "So the next time you watch a model say 'wait', you'll know what you're "
        "seeing. A sixty-four layer network, borrowing a piece of paper.",
    ],
}
