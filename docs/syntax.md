# Описание синтаксиса языка запросов к графам

## Абстрактный синтаксис

```
prog = stmt list

stmt =
    Bind of string * expr
  | Print of expr

expr =
    Var of string                // переменные
  | Int of int
  | Bool of bool
  | String of string             // регулярное выражение, интерпретируемое как единый символ
  | Reg of string                // строковое регулярное выражение, где *, |, . и др. интерпретируются соответствующим образом
  | Cfg of string                // строковая КС-грамматика
  | Set of expr list             // множество элементов одного типа
  | Pair of expr * expr          // пара
  | Edge of expr * expr * expr   // ребро из двух элемнтов и метки
  | SetStarts of expr * expr     // задать множество стартовых состояний
  | SetFinals of expr * expr     // задать множество финальных состояний
  | AddStarts of expr * expr     // добавить состояния в множество стартовых
  | AddFinals of expr * expr     // добавить состояния в множество финальных
  | GetStarts of expr            // получить множество стартовых состояний
  | GetFinals of expr            // получить множество финальных состояний
  | GetReachables of expr        // получить все пары достижимых вершин
  | GetVertices of expr          // получить все вершины
  | GetEdges of expr             // получить все рёбра
  | GetLabels of expr            // получить все метки
  | Map of lambda * expr         // классический map
  | Filter of lambda * expr      // классический filter
  | Load of expr                 // загрузка графа
  | Intersect of expr * expr     // пересечение языков
  | Concat of expr * expr        // конкатенация языков
  | Union of expr * expr         // объединение языков
  | Star of expr                 // замыкание языков (звезда Клини)
  | Contains of expr * expt      // проверка на вхождение элемента в множество

lambda = pattern * expr

pattern =
    Wildcard                               // отбрасывание значения
  | Name of string                         // именование значения
  | Unpair of pattern * pattern            // раскрытие пары
  | Unedge of pattern * pattern * pattern  // раскрытие ребра
```

## Конкретный синтаксис

```
prog -> (COMMENT? ';')* (stmt ((COMMENT? ';')+ stmt)*)? (COMMENT? ';')* EOF

stmt ->
    ID '=' expr
  | 'print' '(' expr ')'

expr ->
    ID                                  // var
  | INT | BOOL | STR | REG | CFG
  | '{' (expr (',' expr)*)? '}'         // Set
  | '(' expr ',' expr ')'               // Pair
  | '(' expr ',' expr ',' expr ')'      // Edge
  | 'set_starts' '(' expr ',' expr ')'
  | 'set_finals' '(' expr ',' expr ')'
  | 'add_starts' '(' expr ',' expr ')'
  | 'add_finals' '(' expr ',' expr ')'
  | 'get_starts' '(' expr ')'
  | 'get_finals' '(' expr ')'
  | 'get_reachables' '(' expr ')'
  | 'get_vertices' '(' expr ')'
  | 'get_edges' '(' expr ')'
  | 'get_labels' '(' expr ')'
  | 'map' '(' lambda ',' expr ')'
  | 'filter' '(' lambda ',' expr ')'
  | 'load' '(' expr ')'
  | expr '&' expr                       // Intersect
  | expr '.' expr                       // Concat
  | expr '|' expr                       // Union
  | expr '*'                            // Star
  | expr 'in' expr                      // Contains
  | '(' expr ')'                        // вложенное выражение

lambda -> '{' pattern '->' expr '}'

pattern ->
    '_'
  | ID
  | '(' pattern ',' pattern ')'
  | '(' pattern ',' pattern ',' pattern ')'

ID -> [a-zA-Z_][a-zA-Z_0-9]*

INT -> '0' | '-'? [1-9][0-9]*
BOOL -> 'true' | 'false'
STR -> '"' .*? '"'
REG -> 'r' STR
CFG -> 'c' STR

COMMENT -> '//' ~[\r\n]*
WS -> [ \t\n\r\f]+
```

## Примеры

Получение вершин, достижимых из определённого множества:

```
g = load("graph.dot");                                                       // FA<int>

// Вариант 1
reachable_pairs = filter({ (s, _) -> s in {1, 2, 42} }, get_reachables(g));  // Set<int * int>
res = map({ (_, f) -> f }, reachable_pairs) ;                                // Set<int>
print(res);

// Вариант 2
g = set_starts({1, 2, 42}, g);                                               // FA<int>
res = map({ (_, f) -> f }, get_reachables(g));                               // Set<int>
print(res)
```

Получение пар вершин, между которыми существует путь, удовлетворяющий КС-ограничению:

```
g = "a" . "b";                                                          // FA<int>
r = c"S -> a S b | a b";                                                // RSM<int>
intersection = g & r;                                                   // RSM<int * int>
res = map({((u, _), (v, _)) -> (u, v)}, get_reachables(intersection));  // Set<int * int>
print(res)
```

Получение вершин, имеющих исходящие рёбра:

```
g = r"a | b | c";                              // FA<int>
print(map({ (v, _, _) -> v }, get_edges(g)))
```
