import logging
import json
import datasets


_CITATION = ''

_DESCRIPTION = ''
_URL = ""
#these three need to be modified accordingly
_TRAINING_FILE = 'classifier_examples_train.json'
_DEV_FILE = 'classifier_examples_test.json'


class text_classConfig(datasets.BuilderConfig):
    """BuilderConfig for text_class"""

    def __init__(self, **kwargs):
        """BuilderConfig for text_class.
        Args:
          **kwargs: keyword arguments forwarded to super.
        """
        super(text_classConfig, self).__init__(**kwargs)


class text_class2021(datasets.GeneratorBasedBuilder):
    """text_class dataset."""

    BUILDER_CONFIGS = [
        text_classConfig(name="text_class", version=datasets.Version("1.0.0"), description="text classification dataset for dstc10 track2"),
    ]

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "title": datasets.Sequence(datasets.Value("string")),
                    "body": datasets.Sequence(datasets.Value("string")),
                    "label": datasets.Sequence(
                        datasets.features.ClassLabel(
                            names=[
                                "true",
                                "false",
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
        }
        downloaded_files = dl_manager.download_and_extract(urls_to_download)

        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={"filepath": downloaded_files["train"]}),
            datasets.SplitGenerator(name=datasets.Split.VALIDATION, gen_kwargs={"filepath": downloaded_files["dev"]}),
        ]
    
    def _generate_examples(self, filepath):
        logging.info("⏳ Generating examples from = %s", filepath)
        with open(filepath, encoding="utf-8") as f:
            dic=json.load(f)
            guid = 0
            title = []
            body = []
            labels = []
            for entry in dic:
                yield guid,{
                    "id": str(guid),
                    "title":entry['title'],
                    'body':entry['body'],
                    'label':entry['label'],
                }
                guid+=1