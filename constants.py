import os

USER_AGENT = os.environ.get('GAG_USER_AGENT', "GAG-Mining (Dr_Lego@ist-einmalig.de)")
DATABASE = os.environ.get('GAG_DATABASE', "/media/raphael/Daten/Wikipedia/gag.sqlite")
WIKIDUMP_DE = os.environ.get('GAG_WIKIDUMP_DE', "/media/raphael/Daten/Wikipedia/dewiki/articles.xml.bz2")
WIKIDUMP_DE_INDEX = os.environ.get('GAG_WIKIDUMP_DE_INDEX', "/media/raphael/Daten/Wikipedia/dewiki/index.txt.bz2")
WIKIDUMP_EN = os.environ.get('GAG_WIKIDUMP_EN', "/media/raphael/Daten/Wikipedia/enwiki/articles.xml.bz2")
WIKIDUMP_EN_INDEX = os.environ.get('GAG_WIKIDUMP_EN_INDEX', "/media/raphael/Daten/Wikipedia/enwiki/index.txt.bz2")