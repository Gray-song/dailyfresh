from haystack import indexes
from goods.models import GoodSKU
#指定对于某个类的某些数据建立索引
class GoodSKUIndex(indexes.SearchIndex, indexes.Indexable):
    #索引字段，document=True表示索引字段。use_template=True索引字段放在指定文件中
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        #返回要被索引的模型类
        return GoodSKU

    # 对该函数返回值建立索引数据
    def index_queryset(self, using=None):

        return self.get_model().objects.all()