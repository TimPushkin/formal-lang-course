# Задача 7. Рекурсивные конечные автоматы

* **Мягкий дедлайн**: 30.10.2022, 23:59
* **Жёсткий дедлайн**: 02.11.2022, 23:59
* Полный балл: 5

## Расширенные контекстно-свободные грамматики (ECFG)

В дополнение к существующему в pyformalng формату описания КС грамматик зафиксируем следующий формат.
- Для каждого нетерминала существует ровно одно правило.
- На одной строке содержится ровно одно правило.
- Правило --- это нетерминал и регулярное выражение над терминалами и нетерминалами, принимаемое pyformalng, разделенные ``` -> ```. Например: ``` S -> a | b* S ```

Будем называть данный формат расширенными контекстно-свободными грамматиками (Extended Context-Free Grammars, ECFG).

## Задача

- [ ] Реализовать тип для представления рекурсивных конечных автоматов. В качестве составных частей можно использовать типы из pyformlang (например, [конечные автоматы](https://pyformlang.readthedocs.io/en/latest/usage.html#finite-automata)). При проектировании этого типа необходимо помнить, что рекурсивные конечные автоматы будут использоваться в алгоритмах КС достижимости, основанных на линейной алгебре, а значит необходимо будет строить матрицы смежности. Здесь могут быть полезны результаты домашних работ по конечным автоматам.
- [ ] Реализовать внутреннее представление для ECFG, пригодное как для дальнейшей конвертации в рекурсивный конечный автомат, так и для получения его из "внешних источников", таких, например, как преобразование из стандартного внутреннего представления КС грамматик в pyformlang.
- [ ] Используя [возможности pyformlang для работы с контекстно-свободными грамматиками](https://pyformlang.readthedocs.io/en/latest/modules/context_free_grammar.html), реализовать **функцию** преобразования контекстно-свободной грамматики в стандартном формате pyformlang в ECFG.
  - Предусмотреть возможность получать исходную грамматику из различных источников. Например, прочитать из файла или получить из преобразования в ОНФХ.
- [ ] Используя [возможности pyformlang для работы с контекстно-свободными грамматиками](https://pyformlang.readthedocs.io/en/latest/modules/context_free_grammar.html), [регулярными выражениями](https://pyformlang.readthedocs.io/en/latest/usage.html#regular-expression) и [конечными автоматами](https://pyformlang.readthedocs.io/en/latest/usage.html#finite-automata), реализовать **функцию** преобразования контекстно-свободной грамматики в ECFG в рекурсивный конечный автомат.
  - Предусмотреть возможность получать исходную грамматику из различных источников. Например, прочитать из файла, прочитать из строковой переменной, получить как результат работы какой-либо другой процедуры.
- [ ] Реализовать **функцию** минимизации рекурсивного конечного автомата. Здесь под минимизацией понимается минимизация автомата для каждого нетерминала как конечного автомата над смешанным алфавитом.
- [ ] Добавить необходимые тесты.
