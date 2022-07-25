import logging

import datasets


_CITATION = ''

_DESCRIPTION = ''
_URL = ""
#these three need to be modified accordingly
_TRAINING_FILE = 'train_ne.txt'
_DEV_FILE = 'valid_ne.txt'
_TEST_FILE = 'train_o.txt'


class simple_ner2021Config(datasets.BuilderConfig):
    """BuilderConfig for simple_ner2021"""

    def __init__(self, **kwargs):
        """BuilderConfig forsimple_ner2021.
        Args:
          **kwargs: keyword arguments forwarded to super.
        """
        super(simple_ner2021Config, self).__init__(**kwargs)


class simple_ner2021(datasets.GeneratorBasedBuilder):
    """simple_ner2021 dataset."""

    BUILDER_CONFIGS = [
        simple_ner2021Config(name="simple_ner2021", version=datasets.Version("1.0.0"), description="simple named entity extraction (2021) dataset"),
    ]

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "tokens": datasets.Sequence(datasets.Value("string")),
                    "ner_tags": datasets.Sequence(
                        datasets.features.ClassLabel(
                            names=[
                                "O",
                                "B-hotel",
                                "I-hotel",
                                "B-restaurant",
                                "I-restaurant",
                                "B-attraction",
                                "I-attraction",
                            ]
                        )
                    ),
                }
            ),
            supervised_keys=None,
            homepage="N/A",
            citation=_CITATION,
        )
    
    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        urls_to_download = {
            "train": f"{_URL}{_TRAINING_FILE}",
            "dev": f"{_URL}{_DEV_FILE}",
            "test": f"{_URL}{_TEST_FILE}",
        }
        downloaded_files = dl_manager.download_and_extract(urls_to_download)

        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={"filepath": downloaded_files["train"]}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={"filepath": downloaded_files["dev"]}),
            datasets.SplitGenerator(name=datasets.Split.TEST, gen_kwargs={"filepath": downloaded_files["test"]}),
        ]
    
    def _generate_examples(self, filepath):
        logging.info("⏳ Generating examples from = %s", filepath)
        with open(filepath, encoding="utf-8") as f:
            guid = 0
            tokens = []
            ner_tags = []
            for line in f:
                if line.startswith("-DOCSTART-") or line == "" or line == "\n":
                    if tokens:
                        yield guid, {
                            "id": str(guid),
                            "tokens": tokens,
                            "ner_tags": ner_tags,
                        }
                        guid += 1
                        tokens = []
                        ner_tags = []
                else:
                    # simple_ner2021 tokens are tab separated
                    splits = line.split("\t")
                    tokens.append(splits[0])
                    ner_tags.append(splits[1].rstrip())
            # last example
            yield guid, {
                "id": str(guid),
                "tokens": tokens,
                "ner_tags": ner_tags,
            }