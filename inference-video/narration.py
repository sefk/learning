"""Narration for each scene, split into beats.

Each beat becomes one audio clip; scenes play one beat's animations while its
clip plays, then wait out whatever audio remains. Numbers come from
analysis/ (measured on the M1 Max) and ../../bench/REPORT.md.

The video is in two parts: mixture of experts, then quantization and context.
"""

SLUG = "local-inference"  # output: local-inference-<part>-<voice>.mp4
CUE_VOICE = "heart"  # the voice the scenes' mid-beat cues were timed against
BEAT_GAP = 0.8  # a slower pace than the thinking video
KOKORO_SPEED = 0.95
SCENES = {  # scene file -> scenes in it
    "scenes_a": ["Hook", "MemoryWall", "Experts"],
    "scenes_b": ["WhatExperts", "MoESpeed", "QwenLineage"],
    "scenes_c": ["Bits", "TwoBits"],
    "scenes_d": ["KVCache", "Caching", "Speculative", "Recap"],
    "scenes_e": ["PartTwo", "Attention", "DeltaNet"],
}
PARTS = {  # part -> scenes, in play order
    "1": ["Hook", "MemoryWall", "Experts", "WhatExperts", "MoESpeed", "Speculative", "QwenLineage"],
    "2": ["PartTwo", "Bits", "TwoBits", "Attention", "DeltaNet", "KVCache", "Caching", "Recap"],
}
CHAPTERS = {
    "Hook": "Two models, one Mac",
    "MemoryWall": "The memory wall",
    "Experts": "Mixture of experts",
    "WhatExperts": "What an expert actually is",
    "MoESpeed": "Why 3.6× faster, not 9×",
    "Speculative": "Speculative decoding",
    "QwenLineage": "Qwen 3 to 3.8",
    "PartTwo": "Where part one left off",
    "Bits": "Quantization",
    "TwoBits": "Is 2-bit workable?",
    "Attention": "Attention and heads",
    "DeltaNet": "Gated DeltaNet",
    "KVCache": "The KV cache",
    "Caching": "Reusing the cache",
    "Recap": "Recap",
}
PRONOUNCE = {
    "DeltaNet": "dˈɛltənˌɛt",
    "MMLU": "ˌɛmˌɛmˌɛlˈju",
    "JSON": "ʤˈeɪsən",
}

NARRATION = {
    "Hook": [
        "Here are two language models, running on the same Mac Studio. Same "
        "family, same generation, both quantized to four bits.",
        "The first is a dense model with twenty-seven billion parameters. It "
        "writes about eighteen and a half tokens per second. The second is "
        "bigger: thirty-five billion parameters. And it writes sixty-seven tokens "
        "per second. Three and a half times faster.",
        "On two standard exams, they score within a point and a half of each "
        "other, which is inside the noise. So the bigger model is faster, and "
        "about as good. How?",
        "Answering that takes us through most of what matters about running a "
        "model locally. In this first part: what limits its speed, and what a "
        "mixture of experts actually is. In part two: what quantization really "
        "costs, and where all your context goes.",
    ],
    "MemoryWall": [
        "Start with what the machine does to produce one token. The model runs "
        "a forward pass: every layer, top to bottom. And in that pass, every "
        "weight in a dense model takes part, so every weight has to be read "
        "from memory and carried to the GPU.",
        "At four bits, the dense model's weights come to about fourteen and a "
        "half gigabytes per token. This machine's memory can move, at best, "
        "four hundred gigabytes per second. Divide, and you get a hard "
        "ceiling: about twenty-eight tokens per second, no matter how fast the "
        "GPU is.",
        "The measured eighteen and a half is two thirds of that ceiling. The "
        "rest of the gap is overhead. The GPU itself is mostly idle, waiting "
        "for memory. Each weight it fetches gets used for just one "
        "multiply and one add, and then it's thrown away until the next token.",
        "Reading the prompt is different. During prefill, the model processes "
        "thousands of prompt tokens at once, so each weight it fetches is used "
        "thousands of times. Now the limit is arithmetic, not memory. The "
        "dense model manages about eighty-nine prompt tokens per second, "
        "which works out to four and a half trillion operations per second.",
        "So inference has two regimes. Prefill, which decides how long you "
        "wait for the first token, is bound by compute. Decode, which decides "
        "how fast the answer streams, is bound by memory bandwidth.",
        "And for decode, there are really only two levers. Touch fewer "
        "weights per token, or make each weight smaller. The first lever is "
        "mixture of experts. The second is quantization.",
    ],
    "Experts": [
        "A transformer layer has two halves. Attention, where tokens look at "
        "each other. And a feed-forward network, which works on each token "
        "on its own. In the dense model, the feed-forward halves hold "
        "seventeen of its twenty-seven billion parameters.",
        "A mixture of experts takes that feed-forward network and chops it "
        "into many small ones. In your Qwen three point six model, every "
        "layer has two hundred fifty-six of them. Each expert is a tiny "
        "network of its own, about three million parameters.",
        "In front of them sits a router: a single small matrix that looks at "
        "the token and gives every expert a score. The top eight scores win. "
        "Those eight experts run, and their outputs are blended, weighted by "
        "their scores. The other two hundred forty-eight do nothing for this "
        "token.",
        "There is also one shared expert that every token goes through, to "
        "hold whatever everyone needs. So per token, per layer, nine small "
        "networks run.",
        "And the choice is made fresh at every one of the forty layers, for "
        "every token. One token passes through three hundred and twenty "
        "routing decisions on its way through the model.",
        "Add it up. The model stores thirty-five billion parameters. But a "
        "single token touches about three billion of them. That's what the "
        "name means: thirty-five B, A three B. Three billion active.",
        "The router is trained along with everything else, with one extra "
        "nudge: a small penalty if some experts get all the traffic while "
        "others sit idle. Without that, training tends to collapse onto a "
        "handful of favourites.",
    ],
    "WhatExperts": [
        "So what is an expert, actually? The name suggests a panel of "
        "specialists. One for chemistry, one for law, one for poetry. To find "
        "out, I hooked the routers of your four-bit model and fed it six "
        "kinds of text: Python, an English short story, math, Chinese, JSON, "
        "and French prose. Then I recorded every choice, at every layer.",
        "In the first layer, the experts sort by the shape of a token, not "
        "its meaning. One expert takes almost nothing but spaces. Another "
        "takes newlines. Whatever the text is about, those tokens go to the "
        "same few experts.",
        "Deeper in, at layer twenty, a pattern appears. Each row here is one "
        "kind of text, each column one of the busiest experts. Many experts "
        "lean clearly toward one kind of text. Some are nearly exclusive: "
        "experts that fire almost only inside JSON, others only inside "
        "Python, others only on Chinese.",
        "But look at what goes together. English and French narration share "
        "more than half their experts. English narration and Python share "
        "twelve percent. The split is by genre and syntax, not by language, "
        "and certainly not by subject.",
        "And the router is rarely sure of itself. Its top choice gets, on "
        "average, four percent of the probability. All eight winners together "
        "get about seventeen. Neighbouring tokens tend to reuse about three of "
        "the same eight experts. That's far more than chance, but it's far "
        "from a fixed specialist per topic.",
        "One more number matters a lot for your memory. A single paragraph of "
        "two hundred tokens touches about half of all ten thousand experts in "
        "the model. You can't load just the experts you'll need. They're all "
        "needed, constantly, so all thirty-five billion parameters stay in "
        "memory.",
        "So an expert is a learned slice of the feed-forward network. Its "
        "specialisation is real, but it's statistical, and it's about the "
        "form of the text more than its subject. Mixture of experts saves "
        "compute and bandwidth. It doesn't save memory.",
    ],
    "MoESpeed": [
        "Now back to speed. Three billion active parameters at four bits is "
        "about one point seven gigabytes per token. That predicts a ceiling "
        "of two hundred and forty tokens per second. The measurement was "
        "sixty-seven, just over a quarter of the ceiling. Where did the rest go?",
        "Part of it is in what a token still has to touch. In this model, "
        "attention isn't sparse: it holds one point three billion parameters, "
        "and every token uses all of them. That's more than the active "
        "experts. Then there's the output layer, which scores all two hundred "
        "and forty-eight thousand vocabulary entries for every token.",
        "The rest is overhead. Forty layers, each a chain of small operations: "
        "route, gather eight experts, run nine tiny networks, blend. Small "
        "operations can't keep the memory system busy, so the time goes to "
        "bookkeeping rather than to moving bytes.",
        "Your benchmarks now include a second mixture model that shows this: "
        "OpenAI's GPT-OSS, with twenty billion parameters. It's built the other "
        "way: thirty-two wide experts with four active, and twenty-four layers "
        "instead of forty. Per token, it reads more bytes than your Qwen model, "
        "two point six gigabytes against one point seven. Yet it writes "
        "eighty-six tokens per second, against sixty-seven. It reaches more "
        "than half its ceiling, where your Qwen model reaches about a quarter. "
        "Fewer, bigger operations keep the memory busy. Its attention is "
        "different too, so this isn't a controlled experiment, but it points "
        "the same way.",
        "Your benchmarks caught this from the other side. Going from four bits to "
        "eight, which doubles the bytes, makes the dense model one point eight "
        "seven times slower. That's almost exactly double, as a "
        "bandwidth-bound model should be. The mixture of experts only slows "
        "by one point two six times, because bandwidth was never most of its "
        "problem.",
        "Prefill gains even more, six point four times, because every prompt "
        "token does about a ninth of the arithmetic. That's why the first "
        "token of an answer arrives in under six seconds instead of over "
        "thirty-six.",
        "Is there a catch on quality? On knowledge and math, no measurable "
        "one. But on code, your benchmarks found the first real difference: the "
        "dense model solved sixty point six percent of the problems, the "
        "mixture fifty point nine. Head to head, twenty-seven problems to "
        "ten. Twenty-six billion parameters applied to every token, against "
        "three, showed up where long, careful reasoning matters most.",
    ],
    "QwenLineage": [
        "Since Qwen is the family you use, it's worth seeing how its experts "
        "have changed. Qwen three, in spring 2025, had a thirty billion "
        "parameter mixture with a hundred and twenty-eight experts, eight "
        "active, and ordinary attention in all forty-eight layers.",
        "Then came Qwen three Next, and the design your three point six model "
        "inherits through three point five. Experts got smaller and more "
        "numerous, a shared expert was added, and three out of every four "
        "attention layers were replaced by something called Gated DeltaNet, "
        "a cheaper kind of attention that we'll take apart in part two. Qwen "
        "three point "
        "six thirty-five B is the same architecture as three point five, "
        "retrained.",
        "Qwen three point eight is mostly a change in training, not in shape. "
        "The configuration files for the three point six and three point "
        "eight twenty-seven B models on your disk are identical, field for "
        "field. Same layers, same widths, same attention. Different weights.",
        "What the new training aimed at shows in the model card Qwen published: big "
        "gains on coding agent tasks. On SWE-bench Pro, from fifty-three and a "
        "half to sixty-one point seven. On Terminal Bench, from sixty-three "
        "to seventy-three. Your "
        "benchmarks measured the other side: seven point four lower on MMLU. "
        "Training for one thing can cost another.",
        "Three point eight also changed the lineup. There is no successor to "
        "your thirty-five B mixture. The open mixture models jumped to "
        "five hundred and twelve experts with ten active: a Flash model of "
        "about a hundred and eighty billion parameters, and a two point four "
        "trillion parameter giant. Neither fits in sixty-four gigabytes.",
        "The Flash model also previews where the architecture goes next. Full "
        "attention is replaced by a sparse version, where a small indexer "
        "picks which earlier tokens are worth attending to. And it adds "
        "fifty-one billion parameters of n-gram embeddings: lookup tables "
        "for common two- and three-token phrases. Like experts, they're "
        "parameters that cost memory, but almost no compute.",
        "That's the first lever: touch fewer weights per token. Your "
        "thirty-five B model reads about a tenth of itself for each token, and "
        "that's where its speed comes from. In part two: the other lever, "
        "making every weight smaller, and the memory that grows as you talk, "
        "the context.",
    ],
    "PartTwo": [
        "This is part two. A quick reminder of where part one left off. To "
        "write each token, your Mac has to read every weight that token uses, "
        "from memory. So speed is roughly memory bandwidth divided by the "
        "bytes each token reads.",
        "Part one covered the first way to shrink that: a mixture of experts, "
        "which touches only about three of your model's thirty-five billion "
        "parameters per token. This part covers the second: quantization, "
        "which makes each parameter smaller. And then the other thing that "
        "fills your memory: the context.",
    ],
    "Bits": [
        "Now the second lever: making each weight smaller. A trained weight "
        "is a sixteen-bit number. Quantization replaces it with a few-bit "
        "integer, plus a little shared information to turn it back into a "
        "number.",
        "Here's how the four-bit builds you run do it. Take sixty-four "
        "consecutive weights. Find their smallest and largest values, and lay "
        "sixteen evenly spaced levels between them. Snap every weight to its "
        "nearest level, and store just the level's number: four bits. Keep "
        "the starting point and the spacing, sixteen bits each, for the "
        "whole group.",
        "That's four bits per weight, plus thirty-two bits shared by sixty-"
        "four weights, which is half a bit more. Four and a half bits per "
        "weight. Your thirty-five billion parameters fit in nineteen and a "
        "half gigabytes.",
        "Every weight is now slightly wrong, by at most half a step. And each "
        "bit you remove doubles the step, which doubles the error. Eight bits "
        "has two hundred fifty-six levels per group. Four bits has sixteen. "
        "Two bits has four.",
        "The builds also don't treat every weight the same. In yours, the "
        "routers are kept at eight bits. They're tiny, and a small error "
        "there sends a token to the wrong experts entirely.",
        "Your benchmarks already settled four versus eight bits. Across "
        "fifteen hundred questions per precision from MMLU, eight bits scored one point "
        "higher, with a standard error of one point four. That's "
        "indistinguishable from zero. Four-bit rounding error is simply "
        "smaller than the differences that decide answers.",
    ],
    "TwoBits": [
        "So what about fewer bits? Is two-bit really workable? I took the "
        "eight-bit build of your model and re-rounded it to fewer bits, then "
        "scored each version on the same five hundred MMLU questions your "
        "benchmarks use.",
        "Rounding everything the same way, four bits barely moves the score: "
        "eighty-five point six percent at eight bits, eighty-five at four. "
        "Three bits loses ten points, down to seventy-five. And two bits "
        "collapses to twenty-eight percent. With four answers to choose from, "
        "guessing scores twenty-five.",
        "The writing is revealing. Asked why the sky is blue, the three-bit "
        "model still answers fluently and correctly. It has lost knowledge, "
        "not language. The two-bit model starts a sentence, then falls into a "
        "loop of ones. And a finer two-bit version, with groups of thirty-two, "
        "writes a perfectly good paragraph about the sky, yet scores "
        "thirty-four percent. Fluent output is no evidence that a quant is "
        "fine.",
        "Now the surprise. Keep everything else at eight bits, and crush only "
        "the experts to two. That model fits in twelve point seven gigabytes "
        "and scores eighty-two percent: smaller than the uniform three-bit "
        "model, and seven points better. The damage at two bits comes mostly "
        "from the small parts that every token passes through: attention, the "
        "shared expert, the embeddings. The experts are ninety-three percent of "
        "the bytes, and they tolerate it far better.",
        "Real low-bit formats build on exactly that. They measure which "
        "weights matter most on sample text, give each tensor its own "
        "precision, and use cleverer codebooks than evenly spaced levels. "
        "That's what the better community quants of large models do. So when "
        "you see a two-bit build, the question is where its bits went. The general rule is that a bigger model at three or four bits "
        "usually beats a smaller model at eight in the same memory, and that "
        "bigger models tolerate fewer bits. Below about three bits, the floor "
        "drops away fast.",
        "And binary? One bit per weight, just the sign, destroys a trained "
        "model outright. The only low-bit models that work are trained that "
        "way from the start. BitNet, for example, uses three values: minus "
        "one, zero, and one. That's about one point six bits. Multiplication "
        "then becomes addition. But you can't get there by rounding a model "
        "that was trained in sixteen bits.",
    ],
    "Attention": [
        "Now, context: everything the model has seen so far, your prompt and "
        "its own answer. To see where it's kept, we need to look at attention, "
        "the half of each layer where tokens look at each other.",
        "When a token arrives, attention turns it into three vectors. A query: "
        "what am I looking for? A key: what do I contain? And a value: what "
        "will I pass along if I'm picked? The new token's query is compared "
        "with the key of every earlier token, and close matches score high.",
        "The scores become weights that add up to one, and the new token takes "
        "that weighted blend of the earlier tokens' values. That's how "
        "information moves between positions. Here, the word it pulls most of "
        "its information from boat.",
        "One comparison can only look for one thing at a time. So attention "
        "runs several side by side, each with its own query, key and value. "
        "These are the heads. One head might track the previous word, another "
        "the subject of the sentence, another the matching bracket in code. "
        "Your model has sixteen heads in each attention layer.",
        "And here's a trick that matters for memory. Your model doesn't give "
        "every head its own keys and values. Its sixteen query heads share "
        "just two sets, eight queries to each. This is called grouped-query "
        "attention. Each head still asks its own question, but they all look "
        "it up in the same shared table.",
        "Every new token has to compare against all the earlier keys and "
        "blend all the earlier values. Recomputing them each time would cost "
        "the whole prompt again, for every token. So they're computed once "
        "and kept. That's the K V cache: K and V for keys and values. It grows "
        "by one entry per token, in every attention layer, and every new "
        "token rereads all of it.",
    ],
    "DeltaNet": [
        "Gated DeltaNet is how Qwen answers that growth: with a memory that "
        "never grows. Instead of a list with one entry per token, each head keeps a "
        "single grid of numbers, a hundred and twenty-eight by a hundred and "
        "twenty-eight. Every token goes into the same grid.",
        "Writing works like this. The token's key and value are multiplied "
        "together into a grid of their own, and added in. Reading goes the "
        "other way. Multiply a query by the grid, and out comes a blend of the "
        "values whose keys look like that query. It's the question attention "
        "asks, answered from a summary instead of a list.",
        "But a plain sum gets muddy. Write two different values under similar "
        "keys, and they pile on top of each other. The delta rule fixes that. "
        "Before writing, the layer reads what the memory already holds for "
        "this key, and writes only the difference between that and the new "
        "value. New information corrects the old, instead of piling on.",
        "The gate is the other half. At every token, the whole grid is "
        "multiplied by a number between zero and one, which the layer picks "
        "based on the token. Near one, the memory holds on. Near zero, it "
        "clears out, say at the start of a new document.",
        "So a DeltaNet layer does the same work for every token, and keeps "
        "the same memory, however long the context. Your model has thirty "
        "of these layers, with thirty-two grids each. Together they take about "
        "sixty-three megabytes, whether the context holds ten tokens or two "
        "hundred thousand.",
        "The price is that a summary is lossy. A fixed grid can't hold every "
        "detail of two hundred thousand tokens, so it can't reliably find one "
        "exact line from far back. That's why Qwen keeps one layer in four as "
        "full attention, with a real cache, for exact recall. Three layers "
        "that summarise, then one that can look anything up.",
    ],
    "KVCache": [
        "Now put numbers on that cache. It lives in the same unified memory as "
        "the weights. And it grows with every token, prompt and answer alike.",
        "Its size per token is simple arithmetic. In your model, each "
        "attention layer stores keys and values for its two shared heads, two "
        "hundred and fifty-six numbers each, in sixteen-bit precision. That's "
        "two kilobytes per layer, per token.",
        "Only ten of the forty layers keep a cache like that. So your mixture "
        "of experts model needs about twenty kilobytes per token. At its full "
        "window of two hundred and sixty-two thousand tokens, that's five and "
        "a half gigabytes. Qwen three's thirty B model, with full attention "
        "everywhere, needed nearly five times as much per token.",
        "The dense model keeps sixteen attention layers, with four shared "
        "heads instead of two: sixty-four kilobytes per token, more than three "
        "times as much. At full length, seventeen gigabytes of cache, more "
        "than its weights.",
        "Long context also costs time, beyond prefill. Every new token has "
        "to read the whole cache as well as the weights. For your mixture of "
        "experts at full length, the cache is three times the size of the "
        "weights each token reads. So decode slows as the conversation "
        "grows.",
    ],
    "Caching": [
        "Because the cache is expensive to build, servers try hard to reuse "
        "it. If a new request starts with exactly the same tokens as the last "
        "one, the server keeps the cache for that shared prefix and only "
        "prefills what's new.",
        "Your benchmarks ran into this. LM Studio, the app that served your "
        "models, prefilled a repeated prompt "
        "eleven point six times faster, fast enough to fake the measurements. "
        "So every prompt had to start with a random nonce to defeat it.",
        "That's also how chat stays fast. Every turn re-sends the whole "
        "conversation, but only the newest message needs prefilling. Edit an "
        "early message, though, and everything after the edit has to be "
        "recomputed.",
        "Hybrid models make one part of this harder. A key-value cache can be "
        "cut back to any earlier point. A DeltaNet state can't. It's one "
        "running summary, and there's no way to subtract tokens back out of "
        "it. To rewind, a server has to have saved a copy at that point.",
        "Hosted models sell the same idea. Their APIs, the interfaces programs "
        "use to call them, offer prompt caching: a cached prefix is billed at "
        "a fraction of the normal price. That's why coding "
        "harnesses keep the system prompt and tool definitions fixed at the "
        "very front, and append everything else after them.",
        "And when the window fills, something has to give. Some harnesses "
        "drop the oldest turns. Others compact them: they ask the model to "
        "summarise the conversation so far, and start a fresh context from "
        "that summary. The session that made this video got compacted "
        "partway through. And some servers just fail. Apple's on-device "
        "model, with a four-thousand-token window, quietly returned empty "
        "answers past it.",
    ],
    "Speculative": [
        "One more idea, because it follows from everything so far. Decode is "
        "bound by reading weights. But once a weight is fetched, using it for "
        "four tokens costs hardly more than using it for one.",
        "So guess ahead. Something cheap proposes the next few tokens. The "
        "big model then checks all of them in a single pass, as if they were "
        "a prompt. It keeps the guesses up to the first one it disagrees with, "
        "and adds its own token there. The output is exactly what the big "
        "model would have written anyway. It just arrives in bursts.",
        "The cheap guesser can be a small draft model from the same family. "
        "Or it can be built in. Your Qwen three point six ships an extra "
        "layer trained for exactly this: multi-token prediction, guessing one "
        "token further ahead. Whether it gets used depends on the server.",
        "It pays best on predictable text, like code and boilerplate. And it "
        "pays less on a mixture of experts: the guessed tokens may each want "
        "different experts, so checking them reads more of the model.",
    ],
    "Recap": [
        "So here's the picture. On your machine, how fast a model writes is "
        "memory bandwidth divided by the bytes each token has to read.",
        "Mixture of experts cuts the weights each token touches, about tenfold "
        "for your model, and turns it into three and a half times the speed. "
        "Quantization cuts the bytes per weight, and four bits costs nothing "
        "you can measure. Hybrid attention cuts the bytes each past token "
        "costs. And speculation squeezes more tokens out of every read.",
        "None of it is free. All the experts still have to sit in memory. "
        "Too few bits, and the model falls apart. Summarised attention "
        "forgets details and can't be rewound. And the dense model still "
        "writes better code.",
        "But it explains the two models we started with. The bigger one is "
        "faster because, for any one token, most of it isn't there.",
    ],
}
