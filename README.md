# Terminology Forced Translation
Set of tools to annotate terminology for forced translation.

## Installation
Just install it from source cloning it
```
git clone https://github.com/zjaume/terminology
cd terminology
pip install .
```

For fast injection during inference, [lttoolbox](https://github.com/apertium/lttoolbox) is required.

## Convert Terminology From TBX Format
First we need to extract terminology from TBX file into JSON format.
```
tbx2json terminology.tbx terminology.json
```

## Create Training Data
Inject terminology annotations in source and target sides for training.
```
cat train.en-de | inject-terms -s en -t de -d terminology.json >train_term.en-de
```

Special tokens for terminology annotation can be specified with `--start-symbol`, `--mid-symbol` and `--end-symbol`.

After that, generated tab-separated data can be used for training.


## Create Apertium Dictionary for Inference
First create dix file with (language direction matters)
```
term2dix -s en -t de terminology.json terminology.en-de.dix
```

then compile the dictionary
```
lt-comp lr terminology.en-de.dix terminology.en-de.bin
```

Now, to use the dictionary for fast terminology injection during inference, just pipe it before the translation command:
```
cat input \
    | sed 's/[]<>@{/}$^\\+[]/\\\0/g' \
    | lt-proc $1 \
    | perl -pe 's#(^|[^\\]|[^\\](\\\\)+)\^(\\\/|[^\/])+[\/]\*?((\\\$|[^\$])+)\$#\1\4#g' \
    | sed 's/\\\([]<>@{/}$^\\+[]\)/\1/g' \
    | translate_command \
    | sed 's/<misc.>//g'
```

The last sed removes `<misc{0,1,2}>` special tags that are the ones used for terminology annotation.
You should reolace it with your own special tokens.
