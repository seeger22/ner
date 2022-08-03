import logging
import json
import datasets


_CITATION = ''

_DESCRIPTION = ''
_URL = ""
#_TRAINING_FILE = 'train_ne.txt'
#_DEV_FILE = 'valid_ne.txt'
#_TEST_FILE = 'train_o.txt'
_KNOWLEDGE_FILE = 'knowledge.json'

class knowledge_base_trainConfig(datasets.BuilderConfig):
    """BuilderConfig for knowledge_base_train"""

    def __init__(self, **kwargs):
        """BuilderConfig for knowledge_base_train.
        Args:
          **kwargs: keyword arguments forwarded to super.
        """
        super(knowledge_base_trainConfig, self).__init__(**kwargs)


class knowledge_base_train(datasets.GeneratorBasedBuilder):
    """knowledge_base_train dataset."""

    BUILDER_CONFIGS = [
        knowledge_base_trainConfig(name="knowledge_base_train", version=datasets.Version("1.0.0"), description="knowledge base for training logs (under simple_ner2021)"),
    ]

    def _info(self):
        return datasets.DatasetInfo(
            description=_DESCRIPTION,
            features=datasets.Features(
                {
                    "id": datasets.Value("string"),
                    "tokens": datasets.Value("string"),
                    "category": datasets.Value("string"),
                    "title":datasets.Sequence(datasets.Value("string")),
                    "body":datasets.Sequence(datasets.Value("string")),
                }
            ),
            supervised_keys=None,
            homepage="N/A",
            citation=_CITATION,
        )
    
    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        urls_to_download = {
            "knowledge": f"{_URL}{_KNOWLEDGE_FILE}",
        }
        downloaded_files = dl_manager.download_and_extract(urls_to_download)

        return [
            datasets.SplitGenerator(name=datasets.Split.TRAIN, gen_kwargs={"filepath": downloaded_files["knowledge"]}),
        ]
    
    def _generate_examples(self, filepath):
        logging.info("⏳ Generating examples from = %s", filepath)
        with open(filepath, encoding="utf-8") as f:
            dic=json.load(f)
            guid = 0
            title=[]
            body=[]
            for cat in dic:
                for elem in dic[cat]:
                    entity=dic[cat][elem]['name']
                    if entity is not None:
                        entity=entity.strip()
                    for conversation in dic[cat][elem]['docs']:
                        title.append(dic[cat][elem]['docs'][conversation]['title'].strip())
                        body.append(dic[cat][elem]['docs'][conversation]['body'].strip())
                    yield guid,{
                        "id":elem,
                        "tokens":entity,
                        "category":cat,
                        "title":title,
                        "body":body,
                    }
                    guid+=1
                    title=[]
                    body=[]