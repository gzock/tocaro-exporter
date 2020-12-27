# 概要

2020年9月1日以降の大規模アップデートが適用された[Tocaro](https://tocaro.im/)からメッセージの一覧をブッコ抜くスクリプト。

大規模アップデート後は、グループやメッセージ取得にREST API使うようになったので、それを利用させてもらっている。  
ブラウザで人間が操作している内容を模倣している感じ。

別のチャットツールなどに移行する際に便利かも？ jsonで出力するので、あとはよしなに。ただし全て自己責任で。

# 動作環境

* Tocaro 768328b8
  * 2020年12月時点のTocaroで各種動作確認済み

* Python 3.6.9

# 使い方

## 下準備

```
$ pip3 install -r requirements.txt
```

## コンフィグの準備

`config.ini`に各種情報を指定する。とりあえず、`email, password`の2つを指定すれば動作する。それぞれのパラメーターの意味について以下に記載する。

パラメーター|デフォルト値|意味
-|-|-
email| - |Tocaroにサインインするためのメールアドレス
password| - |Tocaroにサインインするためのパスワード
group_type|show|メッセージを取得する対象のグループタイプ。show(表示グループ)かhide(非表示グループ)のどちらかを指定する。
excludes|アラート|指定した文字列に部分一致する名前のグループはメッセージ取得しない。
interval|0.3|連続的にメッセージ取得する際の一定の停止間隔(秒)<br>0に指定すると停止なしの最速処理(非推奨)
debug|false|デバッグログを出力するかどうか
path|./outputs|出力先パス

## 実行

所属している全グループから全メッセージを出力。※実行完了までかなり時間がかかる

```
$ ./tocaro_exporter.py --all
```

指定された単一グループの全メッセージのみを出力。

```
$ ./tocaro_exporter.py --group-id [group-id]
```

指定された文字列をグループ名に含むグループの全メッセージを出力。

```
$ ./tocaro_exporter.py --includes [string]
```

所属している全グループの一覧のみを出力。※メッセージの出力は行わない

```
$ ./tocaro_exporter.py --group-only
```

### コンフィグファイルがカレントディレクトリ内に存在しない場合

デフォルトではカレントディレクトリ内の`config.ini`をコンフィグファイルとして読み込む。  
異なるパスやファイル名であった場合は、`--config`によって変更可能。

### オプション一覧

```
./tocaro_exporter.py -h
usage: tocaro_exporter.py [-h] [-c CONFIG] [-a] [-g GROUP_ID] [-i INCLUDES]
                          [--group-only]

Tocaro Exporter

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        specify config file path.
  -a, --all             export all messages from all groups.
  -g GROUP_ID, --group-id GROUP_ID
                        export messages from specified group.
  -i INCLUDES, --includes INCLUDES
                        export message from groups including the specified
                        string.
  --group-only          export for group list json only.
```

# 注意

* TocaroのAPIの都合上、メッセージを30件毎に取得する必要がある。そのためメッセージ量が多いと全てを取得しきるのに相当な時間がかかる。気長に待つべし。
  * 参考程度に・・・以下の条件の全メッセージ出力に1時間程度かかった実績あり
    * グループ/トーク合計数: 110
    * メッセージ総数: 20万弱
    * interval: 0.4
* グループが多いと、その分時間がかかる。不要なグループは非対象になるよう`excludes`には何かしらの文字列は入れておいたほうが良い。
  * `--includes`を併用した場合、excludesによる除外が行われたリストに対して、includesによる処理がかかる

# 参考

* 出力したjsonファイルたちからメッセージ本文だけを抽出して別名で保存するワンライナーコマンド ※bash専用

```
$ for item in `ls outputs/*`; do jq .[].text $item | sed 1~1i--- > ${item/json/txt}; done
```
