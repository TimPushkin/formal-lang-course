# Грамматика для LiteGQL

Для генерации синтаксического анализатора LiteGQL из грамматики ANTLR 4 необходимо выполнить следующие команды:

```shell
pip install antlr4-tools  # На Windows может также потребоваться добавить ANTLR в PATH
antlr4 LiteGQL.g4 -visitor -Dlanguage=Python3
```
