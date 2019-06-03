# coding=utf-8

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from numpy import *

import collections
import csv
import os
import modelingMRC as modeling
import optimization2
import tokenization
import tensorflow as tf
import math
os.environ['CUDA_VISIBLE_DEVICES']='1'
flags = tf.flags

FLAGS = flags.FLAGS

firstTrain = True
## Required parameters
#输入文件路径
flags.DEFINE_string(
    "data_dir", "/home/zju/xlc/bert/bert-master/addressData/finalData",
    "The input data dir. Should contain the .tsv files (or other data files) "
    "for the task.")

#超参文件路径
flags.DEFINE_string(
    # "bert_config_file", "./Address20190113/bert-model/bert_config.json",
    "bert_config_file", "/home/zju/xlc/bert/finalAddress_L-12_H-768_A-12/bert_config.json",
    "The config json file corresponding to the pre-trained BERT model. "
    "This specifies the model architecture.")

#任务名称
flags.DEFINE_string("task_name", "Word2Vec", "The name of the task to train.")

#字典路径
flags.DEFINE_string("vocab_file",
                    # "./Address20190113/bert-model/vocab.txt",
                    "/home/zju/xlc/bert/finalAddress_L-12_H-768_A-12/vocab.txt",
                    "The vocabulary file that the BERT model was trained on.")

#输出文件路径
flags.DEFINE_string(
    "output_dir", "/home/zju/xlc/bert/bert-master/regressResult/finalResult/word2vec3Layers2048-2048-2048",
    "The output directory where the model checkpoints will be written.")

## Other parameters

#初始化模型保存
flags.DEFINE_string(
    "init_checkpoint", "/home/zju/xlc/bert/finalAddress_L-12_H-768_A-12/bert_model.ckpt",
    # "init_checkpoint", "/home/zju/xlc/bert/bert-master/finalClassifierModel/model.ckpt-72071",
    # "init_checkpoint", "/home/zju/xlc/bert/bert-master/regressResult/finalResult/test/model.ckpt-121291",
    "Initial checkpoint (usually from a pre-trained BERT model).")

#是否转成小写
flags.DEFINE_bool(
    "do_lower_case", False,
    "Whether to lower case the input text. Should be True for uncased "
    "models and False for cased models.")

#句子最大长度
flags.DEFINE_integer(
    "max_seq_length", 51,
    "The maximum total input sequence length after WordPiece tokenization. "
    "Sequences longer than this will be truncated, and sequences shorter "
    "than this will be padded.")

#是否训练
flags.DEFINE_bool("do_train", True, "Whether to run training.")

#是否评估
flags.DEFINE_bool("do_eval", True, "Whether to run eval on the dev set.")

#是否预测
flags.DEFINE_bool(
    "do_predict", True,
    "Whether to run the model in inference mode on the test set.")

#训练的batchsize
flags.DEFINE_integer("train_batch_size", 64, "Total batch size for training.")

#评估的batchsize
flags.DEFINE_integer("eval_batch_size", 64, "Total batch size for eval.")

#预测的batchsize
flags.DEFINE_integer("predict_batch_size", 64, "Total batch size for predict.")

#学习率
flags.DEFINE_float("learning_rate", 0.0001, "The initial learning rate for Adam.")

#训练轮数
flags.DEFINE_float("num_train_epochs", 5.0,
                   "Total number of training epochs to perform.")
#预热阶段的百分比
flags.DEFINE_float(
    "warmup_proportion", 0.0,
    "Proportion of training to perform linear learning rate warmup for. "
    "E.g., 0.1 = 10% of training.")

#每多少步保存一次
flags.DEFINE_integer("save_checkpoints_steps", 500,
                     "How often to save the model checkpoint.")

flags.DEFINE_integer("iterations_per_loop", 500,
                     "How many steps to make in each estimator call.")

flags.DEFINE_bool("use_tpu", False, "Whether to use TPU or GPU/CPU.")

tf.flags.DEFINE_string(
    "tpu_name", None,
    "The Cloud TPU to use for training. This should be either the name "
    "used when creating the Cloud TPU, or a grpc://ip.address.of.tpu:8470 "
    "url.")

tf.flags.DEFINE_string(
    "tpu_zone", None,
    "[Optional] GCE zone where the Cloud TPU is located in. If not "
    "specified, we will attempt to automatically detect the GCE project from "
    "metadata.")

tf.flags.DEFINE_string(
    "gcp_project", None,
    "[Optional] Project name for the Cloud TPU-enabled project. If not "
    "specified, we will attempt to automatically detect the GCE project from "
    "metadata.")

tf.flags.DEFINE_string("master", None, "[Optional] TensorFlow master URL.")

flags.DEFINE_integer(
    "num_tpu_cores", 8,
    "Only used if `use_tpu` is True. Total number of TPU cores to use.")


class InputExample(object):
  """A single training/test example for simple sequence classification."""

  def __init__(self, guid, text_a, text_b=None, word2vec_sentance=None,results=None):
    """Constructs a InputExample.

    Args:
      guid: Unique id for the example.
      text_a: string. The untokenized text of the first sequence. For single
        sequence tasks, only this sequence must be specified.
      text_b: (Optional) string. The untokenized text of the second sequence.
        Only must be specified for sequence pair tasks.
      results: (Optional) string. The label of the example. This should be
        specified for train and dev examples, but not for test examples.
    """
    self.guid = guid
    self.text_a = text_a
    self.text_b = text_b
    self.word2vec_sentance = word2vec_sentance
    self.results = results


class InputFeatures(object):
  """A single set of features of data."""

  def __init__(self, word2vec_sentance,the_results):
    self.word2vec_sentance = word2vec_sentance
    self.the_results = the_results


class DataProcessor(object):
  """Base class for data converters for sequence classification data sets."""

  def get_train_examples(self, data_dir):
    """Gets a collection of `InputExample`s for the train set."""
    raise NotImplementedError()

  def get_dev_examples(self, data_dir):
    """Gets a collection of `InputExample`s for the dev set."""
    raise NotImplementedError()

  def get_test_examples(self, data_dir):
    """Gets a collection of `InputExample`s for prediction."""
    raise NotImplementedError()

  @classmethod
  def _read_tsv(cls, input_file, quotechar=None):
    """Reads a tab separated value file."""
    with tf.gfile.Open(input_file, "r") as f:
      reader = csv.reader(f, delimiter="\t", quotechar=quotechar)
      lines = []
      for line in reader:
        lines.append(line)
      return lines

#word2vec的processor
class Word2VecProcessor(DataProcessor):
    def get_train_examples(self, data_dir):
        """See base class."""
        with open('/home/zju/xlc/bert/bert-master/addressData/finalData/final_w2vec_real_right_regress_train.csv', 'r') as a1:
            l1 = a1.readlines()
            return self._create_examples(l1, "train")
        # return self._create_examples(
        #     self._read_tsv(os.path.join(data_dir, "final_real_right_regress_train.tsv")), "train")

    def get_dev_examples(self, data_dir):
        """See base class."""
        with open('/home/zju/xlc/bert/bert-master/addressData/finalData/final_w2vec_real_right_regress_eval.csv', 'r') as a2:
            l2 = a2.readlines()
            return self._create_examples(l2, "eval")

    def get_test_examples(self, data_dir):
        """See base class."""
        with open('/home/zju/xlc/bert/bert-master/addressData/finalData/final_w2vec_real_right_regress_predict.csv', 'r') as a3:
            l3 = a3.readlines()
            return self._create_examples(l3, "predict")

    def _create_examples(self, lines, set_type):
        """Creates examples for the training and dev sets."""
        examples = []
        aa = loadtxt('/home/zju/xlc/bert/bert-master/addressData/finalData_vecOnly.txt')
        with open('/home/zju/xlc/bert/bert-master/addressData/finalData_vec.txt','r') as ff1:
            lin1 = ff1.readlines()
            wordDict = {}
            for l in range(len(lin1)):
                wordDict[lin1[l].split(' ')[0]] = aa[l]

            for (i, line) in enumerate(lines):
            # guid = "%s-%s" % (set_type, i)
                transition = line.split(',')[2].strip('\n')
                textAddress = transition.split(' ')
                a = wordDict[textAddress[0]]
                for j in range(len(textAddress)-1):
                    a = a + wordDict[textAddress[j+1]]
                a = a / len(textAddress)
                results = [((float(line.split(',')[0]) - 1090000)), ((float(line.split(',')[1]) - 3360000))]
                examples.append(
                    InputExample(guid=None, text_a=None, text_b=None, word2vec_sentance=a, results=results))
        return examples

def convert_single_example(ex_index, example, max_seq_length,
                           tokenizer):
  """Converts a single `InputExample` into a single `InputFeatures`."""

  tokens_a = tokenizer.tokenize(example.text_a)
  tokens_b = None
  if example.text_b:
    tokens_b = tokenizer.tokenize(example.text_b)

  if tokens_b:
    # Modifies `tokens_a` and `tokens_b` in place so that the total
    # length is less than the specified length.
    # Account for [CLS], [SEP], [SEP] with "- 3"
    _truncate_seq_pair(tokens_a, tokens_b, max_seq_length - 3)
  else:
    # Account for [CLS] and [SEP] with "- 2"
    if len(tokens_a) > max_seq_length - 2:
      tokens_a = tokens_a[0:(max_seq_length - 2)]

  # The convention in BERT is:
  # (a) For sequence pairs:
  #  tokens:   [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
  #  type_ids: 0     0  0    0    0     0       0 0     1  1  1  1   1 1
  # (b) For single sequences:
  #  tokens:   [CLS] the dog is hairy . [SEP]
  #  type_ids: 0     0   0   0  0     0 0
  #
  # Where "type_ids" are used to indicate whether this is the first
  # sequence or the second sequence. The embedding vectors for `type=0` and
  # `type=1` were learned during pre-training and are added to the wordpiece
  # embedding vector (and position vector). This is not *strictly* necessary
  # since the [SEP] token unambiguously separates the sequences, but it makes
  # it easier for the model to learn the concept of sequences.
  #
  # For classification tasks, the first vector (corresponding to [CLS]) is
  # used as as the "sentence vector". Note that this only makes sense because
  # the entire model is fine-tuned.
  tokens = []
  segment_ids = []
  tokens.append("[CLS]")
  segment_ids.append(0)
  for token in tokens_a:
    tokens.append(token)
    segment_ids.append(0)
  tokens.append("[SEP]")
  segment_ids.append(0)

  if tokens_b:
    for token in tokens_b:
      tokens.append(token)
      segment_ids.append(1)
    tokens.append("[SEP]")
    segment_ids.append(1)

  input_ids = tokenizer.convert_tokens_to_ids(tokens)

  # The mask has 1 for real tokens and 0 for padding tokens. Only real
  # tokens are attended to.
  input_mask = [1] * len(input_ids)

  # Zero-pad up to the sequence length.
  while len(input_ids) < max_seq_length:
    input_ids.append(0)
    input_mask.append(0)
    segment_ids.append(0)

  assert len(input_ids) == max_seq_length
  assert len(input_mask) == max_seq_length
  assert len(segment_ids) == max_seq_length

  if ex_index < 5:
    tf.logging.info("*** Example ***")
    tf.logging.info("guid: %s" % example.guid)
    tf.logging.info("tokens: %s" % " ".join(
        [tokenization.printable_text(x) for x in tokens]))
    tf.logging.info("input_ids: %s" % " ".join([str(x) for x in input_ids]))
    tf.logging.info("input_mask: %s" % " ".join([str(x) for x in input_mask]))
    tf.logging.info("segment_ids: %s" % " ".join([str(x) for x in segment_ids]))
    tf.logging.info("lon:%s-lat:%s" % (example.results[0], example.results[1]))

  feature = InputFeatures(
      word2vec_sentance=example.word2vec_sentance,
      the_results=example.results
    )
  return feature


def file_based_convert_examples_to_features(
    examples, max_seq_length, tokenizer, output_file):
  """Convert a set of `InputExample`s to a TFRecord file."""

  writer = tf.python_io.TFRecordWriter(output_file)

  for (ex_index, example) in enumerate(examples):
    if ex_index % 10000 == 0:
      tf.logging.info("Writing example %d of %d" % (ex_index, len(examples)))

    # feature = convert_single_example(ex_index, example,
    #                                  max_seq_length, tokenizer)

    def create_int_feature(values):
      f = tf.train.Feature(int64_list=tf.train.Int64List(value=list(values)))
      return f
    def create_float_feature(values):
      f = tf.train.Feature(float_list=tf.train.FloatList(value=list(values)))
      return f

    features = collections.OrderedDict()
    # features["input_ids"] = create_int_feature(feature.input_ids)
    # features["input_mask"] = create_int_feature(feature.input_mask)
    # features["segment_ids"] = create_int_feature(feature.segment_ids)
    features["word2vec_sentance"] = create_float_feature(example.word2vec_sentance)
    features["the_results"] = create_float_feature(example.results)

    tf_example = tf.train.Example(features=tf.train.Features(feature=features))
    writer.write(tf_example.SerializeToString())


def file_based_input_fn_builder(input_file, seq_length, is_training,
                                drop_remainder):
  """Creates an `input_fn` closure to be passed to TPUEstimator."""

  name_to_features = {
      # "input_ids": tf.FixedLenFeature([seq_length], tf.int64),
      # "input_mask": tf.FixedLenFeature([seq_length], tf.int64),
      # "segment_ids": tf.FixedLenFeature([seq_length], tf.int64),
      "word2vec_sentance": tf.FixedLenFeature([768], tf.float32),
      "the_results": tf.FixedLenFeature([2], tf.float32)
  }

  def _decode_record(record, name_to_features):
    """Decodes a record to a TensorFlow example."""
    example = tf.parse_single_example(record, name_to_features)

    # tf.Example only supports tf.int64, but the TPU only supports tf.int32.
    # So cast all int64 to int32.
    for name in list(example.keys()):
      t = example[name]
      if t.dtype == tf.int64:
        t = tf.to_int32(t)
      example[name] = t

    return example

  def input_fn(params):
    """The actual input function."""
    batch_size = params["batch_size"]

    # For training, we want a lot of parallel reading and shuffling.
    # For eval, we want no shuffling and parallel reading doesn't matter.
    d = tf.data.TFRecordDataset(input_file)
    if is_training and firstTrain:
      d = d.repeat()
      d = d.shuffle(buffer_size=1550000)

    d = d.apply(
        tf.contrib.data.map_and_batch(
            lambda record: _decode_record(record, name_to_features),
            batch_size=batch_size,
            drop_remainder=drop_remainder))

    return d

  return input_fn


def _truncate_seq_pair(tokens_a, tokens_b, max_length):
  """Truncates a sequence pair in place to the maximum length."""

  # This is a simple heuristic which will always truncate the longer sequence
  # one token at a time. This makes more sense than truncating an equal percent
  # of tokens from each, since if one sequence is very short then each token
  # that's truncated likely contains more information than a longer sequence.
  while True:
    total_length = len(tokens_a) + len(tokens_b)
    if total_length <= max_length:
      break
    if len(tokens_a) > len(tokens_b):
      tokens_a.pop()
    else:
      tokens_b.pop()


def create_model(bert_config, is_training, word2vec_sentance,
                 the_results, use_one_hot_embeddings):
  """Creates a classification model."""
  # model = modeling.BertModel(
  #     config=bert_config,
  #     is_training=is_training,
  #     input_ids=input_ids,
  #     input_mask=input_mask,
  #     token_type_ids=segment_ids,
  #     use_one_hot_embeddings=use_one_hot_embeddings)

  # segment.
  # In the demo, we are doing a simple classification task on the entire
  #
  # If you want to use the token-level output, use model.get_sequence_output()
  # instead.

  #output_layer = model.get_pooled_output()
  output_layer = word2vec_sentance
  #output_layer = tf.reduce_mean(model.get_sequence_output(),1)

  with tf.variable_scope("loss"):
    if is_training:
        # I.e., 0.1 dropout
        output_layer = tf.nn.dropout(output_layer, keep_prob=0.9)
        # 为经纬度回归自己添加的部分，修改处1
    firstLayer = tf.layers.dense(
            output_layer,
            2048,
            activation=tf.nn.relu,
            kernel_initializer=tf.truncated_normal_initializer(stddev=0.02))
    firstLayer = tf.nn.dropout(firstLayer, keep_prob=0.9)
    secondLayer = tf.layers.dense(
            firstLayer,
            2048,
            activation=tf.nn.relu,
            kernel_initializer=tf.truncated_normal_initializer(stddev=0.02))
    secondLayer = tf.nn.dropout(secondLayer, keep_prob=0.9)
    thirdLayer = tf.layers.dense(
            secondLayer,
            2048,
            activation=tf.nn.relu,
            kernel_initializer=tf.truncated_normal_initializer(stddev=0.02))
    thirdLayer = tf.nn.dropout(thirdLayer, keep_prob=0.9)
    outputResult = tf.layers.dense(
        thirdLayer,
            2)
    per_example_loss = tf.sqrt(tf.square(outputResult[0]-the_results[0])+tf.square(outputResult[1]-the_results[1]))
    loss = tf.reduce_mean(per_example_loss)
    return loss, per_example_loss, outputResult

def model_fn_builder(bert_config, init_checkpoint, learning_rate,
                     num_train_steps, num_warmup_steps, use_tpu,
                     use_one_hot_embeddings):
  """Returns `model_fn` closure for TPUEstimator."""

  def model_fn(features, labels, mode, params):  # pylint: disable=unused-argument
    """The `model_fn` for TPUEstimator."""

    tf.logging.info("*** Features ***")
    for name in sorted(features.keys()):
      tf.logging.info("  name = %s, shape = %s" % (name, features[name].shape))

    # input_ids = features["input_ids"]
    # input_mask = features["input_mask"]
    # segment_ids = features["segment_ids"]
    word2vec_sentance = features["word2vec_sentance"]
    the_results = features["the_results"]

    is_training = (mode == tf.estimator.ModeKeys.TRAIN)

    (total_loss, per_example_loss, predi) = create_model(
        bert_config, is_training, word2vec_sentance, the_results,
        use_one_hot_embeddings)

    tvars = tf.trainable_variables()
    initialized_variable_names = {}
    scaffold_fn = None
    if init_checkpoint:
      (assignment_map, initialized_variable_names) = modeling.get_assignment_map_from_checkpoint(tvars, init_checkpoint)
      if use_tpu:

        def tpu_scaffold():
          tf.train.init_from_checkpoint(init_checkpoint, assignment_map)
          return tf.train.Scaffold()

        scaffold_fn = tpu_scaffold
      else:
        tf.train.init_from_checkpoint(init_checkpoint, assignment_map)

    tf.logging.info("**** Trainable Variables ****")
    for var in tvars:
      init_string = ""
      if var.name in initialized_variable_names:
        init_string = ", *INIT_FROM_CKPT*"
      tf.logging.info("  name = %s, shape = %s%s", var.name, var.shape,
                      init_string)

    output_spec = None
    if mode == tf.estimator.ModeKeys.TRAIN:

      train_op = optimization2.create_optimizer(total_loss, learning_rate, num_train_steps, num_warmup_steps, use_tpu)
      logging_hook = tf.train.LoggingTensorHook({'loss':total_loss}, every_n_iter=100)
      data_hook = tf.train.LoggingTensorHook({'lonlat':the_results}, every_n_iter=1)
      # data_hook = tf.train.LoggingTensorHook({'gradients': tf.gradients(total_loss, tvars)}, every_n_iter=1)

      # output_vars = tf.trainable_variables(scope='loss')
      # my_opt = tf.train.AdamOptimizer(0.5).minimize(total_loss, var_list = output_vars, global_step=tf.train.get_or_create_global_step())
      # my_opt = tf.train.GradientDescentOptimizer(0.000005)
      # train_step = my_opt.minimize(total_loss, global_step=tf.train.get_or_create_global_step())
      output_spec = tf.contrib.tpu.TPUEstimatorSpec(
          mode=mode,
          loss=total_loss,
          train_op=train_op,
          training_hooks=[logging_hook],
          scaffold_fn=scaffold_fn)
    elif mode == tf.estimator.ModeKeys.EVAL:

      def metric_fn(per_example_loss):
        loss = tf.metrics.mean(per_example_loss)
        return {
            "eval_loss": loss
        }

      eval_metrics = (metric_fn, [total_loss])
      output_spec = tf.contrib.tpu.TPUEstimatorSpec(
          mode=mode,
          loss=total_loss,
          eval_metrics=eval_metrics,
          scaffold_fn=scaffold_fn)
    else:
      predictions = {
            "results":the_results,
            "prediction": predi

      }
      output_spec = tf.contrib.tpu.TPUEstimatorSpec(
          mode=mode, predictions=predictions, scaffold_fn=scaffold_fn)
    return output_spec

  return model_fn

def main(_):
  tf.logging.set_verbosity(tf.logging.INFO)

  processors = {
      "word2vec": Word2VecProcessor,
  }

  if not FLAGS.do_train and not FLAGS.do_eval and not FLAGS.do_predict:
    raise ValueError(
        "At least one of `do_train`, `do_eval` or `do_predict' must be True.")

  bert_config = modeling.BertConfig.from_json_file(FLAGS.bert_config_file)

  if FLAGS.max_seq_length > bert_config.max_position_embeddings:
    raise ValueError(
        "Cannot use sequence length %d because the BERT model "
        "was only trained up to sequence length %d" %
        (FLAGS.max_seq_length, bert_config.max_position_embeddings))

  tf.gfile.MakeDirs(FLAGS.output_dir)

  task_name = FLAGS.task_name.lower()

  if task_name not in processors:
    raise ValueError("Task not found: %s" % (task_name))

  processor = processors[task_name]()

  tokenizer = tokenization.FullTokenizer(
      vocab_file=FLAGS.vocab_file, do_lower_case=FLAGS.do_lower_case)

  tpu_cluster_resolver = None
  if FLAGS.use_tpu and FLAGS.tpu_name:
    tpu_cluster_resolver = tf.contrib.cluster_resolver.TPUClusterResolver(
        FLAGS.tpu_name, zone=FLAGS.tpu_zone, project=FLAGS.gcp_project)

  is_per_host = tf.contrib.tpu.InputPipelineConfig.PER_HOST_V2
  run_config = tf.contrib.tpu.RunConfig(
      cluster=tpu_cluster_resolver,
      master=FLAGS.master,
      model_dir=FLAGS.output_dir,
      save_checkpoints_steps=FLAGS.save_checkpoints_steps,
      tpu_config=tf.contrib.tpu.TPUConfig(
          iterations_per_loop=FLAGS.iterations_per_loop,
          num_shards=FLAGS.num_tpu_cores,
          per_host_input_for_training=is_per_host))

  train_examples = None
  num_train_steps = None
  num_warmup_steps = None
  if FLAGS.do_train:
    train_examples = processor.get_train_examples(FLAGS.data_dir)
    num_train_steps = int(
        len(train_examples) / FLAGS.train_batch_size * FLAGS.num_train_epochs)
    num_warmup_steps = int(num_train_steps * FLAGS.warmup_proportion)

  model_fn = model_fn_builder(
      bert_config=bert_config,
      init_checkpoint=FLAGS.init_checkpoint,
      learning_rate=FLAGS.learning_rate,
      num_train_steps=num_train_steps,
      num_warmup_steps=num_warmup_steps,
      use_tpu=FLAGS.use_tpu,
      use_one_hot_embeddings=FLAGS.use_tpu)

  # If TPU is not available, this will fall back to normal Estimator on CPU
  # or GPU.
  estimator = tf.contrib.tpu.TPUEstimator(
      use_tpu=FLAGS.use_tpu,
      model_fn=model_fn,
      config=run_config,
      train_batch_size=FLAGS.train_batch_size,
      eval_batch_size=FLAGS.eval_batch_size,
      predict_batch_size=FLAGS.predict_batch_size)

  if FLAGS.do_train:
    train_file = os.path.join(FLAGS.output_dir, "train.tf_record")
    #在有tfrecord的情况下注释避免再次生成
    # file_based_convert_examples_to_features(
    #     train_examples, FLAGS.max_seq_length, tokenizer, train_file)
    # tf.logging.info("***** Running training *****")
    # tf.logging.info("  Num examples = %d", len(train_examples))
    # tf.logging.info("  Batch size = %d", FLAGS.train_batch_size)
    # tf.logging.info("  Num steps = %d", num_train_steps)
    train_input_fn = file_based_input_fn_builder(
        input_file=train_file,
        seq_length=FLAGS.max_seq_length,
        is_training=True,
        drop_remainder=True)
    # estimator.train(input_fn=train_input_fn, max_steps=num_train_steps)

  if FLAGS.do_eval:
    eval_examples = processor.get_dev_examples(FLAGS.data_dir)
    eval_file = os.path.join(FLAGS.output_dir, "eval.tf_record")
    file_based_convert_examples_to_features(
        eval_examples, FLAGS.max_seq_length, tokenizer, eval_file)

    tf.logging.info("***** Running evaluation *****")
    tf.logging.info("  Num examples = %d", len(eval_examples))
    tf.logging.info("  Batch size = %d", FLAGS.eval_batch_size)

    # This tells the estimator to run through the entire set.
    eval_steps = None
    # However, if running eval on the TPU, you will need to specify the
    # number of steps.
    if FLAGS.use_tpu:
      # Eval will be slightly WRONG on the TPU because it will truncate
      # the last batch.
      eval_steps = int(len(eval_examples) / FLAGS.eval_batch_size)

    eval_drop_remainder = True if FLAGS.use_tpu else False
    eval_input_fn = file_based_input_fn_builder(
        input_file=eval_file,
        seq_length=FLAGS.max_seq_length,
        is_training=False,
        drop_remainder=eval_drop_remainder)

    # result = estimator.evaluate(input_fn=eval_input_fn, steps=eval_steps)
    #
    # output_eval_file = os.path.join(FLAGS.output_dir, "eval_results.txt")
    # with tf.gfile.GFile(output_eval_file, "w") as writer:
    #     tf.logging.info("***** Eval results *****")
    #     for key in sorted(result.keys()):
    #         tf.logging.info("  %s = %s", key, str(result[key]))
    #         writer.write("%s = %s\n" % (key, str(result[key])))

  if FLAGS.do_predict:
    predict_examples = processor.get_test_examples(FLAGS.data_dir)
    predict_file = os.path.join(FLAGS.output_dir, "predict.tf_record")
    file_based_convert_examples_to_features(predict_examples,
                                            FLAGS.max_seq_length, tokenizer,
                                            predict_file)

    tf.logging.info("***** Running prediction*****")
    tf.logging.info("  Num examples = %d", len(predict_examples))
    tf.logging.info("  Batch size = %d", FLAGS.predict_batch_size)

    if FLAGS.use_tpu:
      # Warning: According to tpu_estimator.py Prediction on TPU is an
      # experimental feature and hence not supported here
      raise ValueError("Prediction in TPU not supported")

    predict_drop_remainder = True if FLAGS.use_tpu else False
    predict_input_fn = file_based_input_fn_builder(
        input_file=predict_file,
        seq_length=FLAGS.max_seq_length,
        is_training=False,
        drop_remainder=predict_drop_remainder)

    # result = estimator.predict(input_fn=predict_input_fn, yield_single_examples=True)

    # output_predict_file = os.path.join(FLAGS.output_dir, "test_results.tsv")
    # with tf.gfile.GFile(output_predict_file, "w") as writer:
    #   tf.logging.info("***** Predict results *****")
    #   for prediction in result:
    #     # output_line = "\t".join(
    #     #     str(class_probability) for class_probability in prediction) + "\n"
    #
    #     x = prediction['prediction'][0]+1090000
    #     y = prediction['prediction'][1]+3360000
    #     truex = prediction['results'][0]+1090000
    #     truey = prediction['results'][1]+3360000
    #     output_line = str(x) + "\t" + str(y) + "\t" + str(truex) + "\t" + str(truey) + "\n"
    #     writer.write(output_line)

  if FLAGS.do_train and FLAGS.do_eval and FLAGS.do_predict:
      now_step = 0
      while now_step < num_train_steps:
          now_step = now_step+500
          result = estimator.evaluate(input_fn=eval_input_fn, steps=eval_steps)
          output_eval_file = os.path.join(FLAGS.output_dir, "eval_results.txt")
          with tf.gfile.GFile(output_eval_file, "w") as writer:
              tf.logging.info("***** Eval results *****")
              for key in sorted(result.keys()):
                  tf.logging.info("  %s = %s", key, str(result[key]))
                  writer.write("%s = %s\n" % (key, str(result[key])))

          preResult = estimator.predict(input_fn=predict_input_fn, yield_single_examples=True)
          output_evalRecord_file = os.path.join(FLAGS.output_dir, "evalRecord", "test_results"+ str(now_step) +".tsv")
          with tf.gfile.GFile(output_evalRecord_file, "w") as writer:
              tf.logging.info("***** evalRecord results *****")
              for prediction in preResult:
                  x = abs(prediction['prediction'][0] - prediction['results'][0])
                  y = abs(prediction['prediction'][1] - prediction['results'][1])
                  dis = math.sqrt(x*x + y*y)
                  output_line = str(dis) + "\n"
                  writer.write(output_line)

          estimator.train(input_fn=train_input_fn, steps=500)
          firstTrain = False

if __name__ == "__main__":
  flags.mark_flag_as_required("data_dir")
  flags.mark_flag_as_required("task_name")
  flags.mark_flag_as_required("vocab_file")
  flags.mark_flag_as_required("bert_config_file")
  flags.mark_flag_as_required("output_dir")
  tf.app.run()
