grammar LiteGQL;

prog : (COMMENT? SEMI)* (stmt ((COMMENT? SEMI)+ stmt)*)? (COMMENT? SEMI)* EOF ;

stmt :
    PRINT LPAREN expr RPAREN                  # print
  | ID EQUALS expr                            # bind
  ;

expr :
    SET_STARTS LPAREN expr COMMA expr RPAREN  # setStarts
  | SET_FINALS LPAREN expr COMMA expr RPAREN  # setFinals
  | ADD_STARTS LPAREN expr COMMA expr RPAREN  # addStarts
  | ADD_FINALS LPAREN expr COMMA expr RPAREN  # addFinals
  | GET_STARTS LPAREN expr RPAREN             # getStarts
  | GET_FINALS LPAREN expr RPAREN             # getFinals
  | GET_REACHABLES LPAREN expr RPAREN         # getReachables
  | GET_VERTICES LPAREN expr RPAREN           # getVertices
  | GET_EDGES LPAREN expr RPAREN              # getEdges
  | GET_LABELS LPAREN expr RPAREN             # getLabels
  | MAP LPAREN lambda COMMA expr RPAREN       # map
  | FILTER LPAREN lambda COMMA expr RPAREN    # filter
  | LOAD LPAREN expr RPAREN                   # load
  | INT                                       # int
  | BOOL                                      # bool
  | STR                                       # string
  | REG                                       # reg
  | CFG                                       # cfg
  | ID                                        # var
  | LCURLY (expr (COMMA expr)*)? RCURLY       # set
  | LPAREN expr COMMA expr RPAREN             # pair
  | LPAREN expr COMMA expr COMMA expr RPAREN  # edge
  | expr ASTER                                # star
  | expr DOT expr                             # concat
  | expr AMPER expr                           # intersect
  | expr VLINE expr                           # union
  | expr IN expr                              # contains
  | LPAREN expr RPAREN                        # parens
  ;

lambda : LCURLY pattern RARROW expr RCURLY ;

pattern :
    UNDER                                              # wildcard
  | ID                                                 # name
  | LPAREN pattern COMMA pattern RPAREN                # unpair
  | LPAREN pattern COMMA pattern COMMA pattern RPAREN  # unedge
  ;

SEMI : ';' ;

LPAREN : '(' ;
RPAREN : ')' ;
LCURLY : '{' ;
RCURLY : '}' ;

EQUALS : '=' ;
COMMA : ',' ;
RARROW : '->' ;
UNDER : '_' ;

ASTER : '*' ;
DOT : '.' ;
AMPER : '&' ;
VLINE : '|' ;
IN : 'in' ;

PRINT : 'print' ;

SET_STARTS : 'set_starts' ;
SET_FINALS : 'set_finals' ;
ADD_STARTS : 'add_starts' ;
ADD_FINALS : 'add_finals' ;
GET_STARTS : 'get_starts' ;
GET_FINALS : 'get_finals' ;
GET_REACHABLES : 'get_reachables' ;
GET_VERTICES : 'get_vertices' ;
GET_EDGES : 'get_edges' ;
GET_LABELS : 'get_labels' ;
MAP : 'map' ;
FILTER : 'filter' ;
LOAD : 'load' ;

INT : '0' | '-'? [1-9][0-9]* ;
BOOL : 'true' | 'false' ;
STR : '"' .*? '"' ;
REG : 'r' STR ;
CFG : 'c' STR ;

ID : [_a-zA-Z][_a-zA-Z0-9]* ;

COMMENT : '//' ~[\r\n]* -> skip ;
WS : [ \n\r\t\f]+ -> skip ;
