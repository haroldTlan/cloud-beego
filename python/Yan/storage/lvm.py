import re
from ply import lex, yacc
import os

class LVMMetadataLexer(object):
    tokens = (
        'INT',
        'FLOAT',
        'STRING',
        'ID'
    )

    def __init__(self):
        self.lexer = lex.lex(module=self)

    def __iter__(self):
        return iter(self.lexer)

    def token(self):
        return self.lexer.token()

    t_ID = r'[-_0-9a-zA-Z]+'

    literals = ['=', '{', '}', '[', ']', ',']

    def t_FLOAT(self, t):
        r'(0|[1-9][0-9]*)([.][0-9]*)?([eE][+-]?[0-9]+)?'
        if '.' in t.value or 'e' in t.value:
            t.value = float(t.value)
        else:
            t.type = 'INT'
            t.value = int(t.value)
        return t

    def t_STRING(self, t):
        r'".+?"'
        t.value = t.value[1:-1]
        return t

    def t_ignore_whitespace(self, t):
        r'\s+'
        pass

    def t_ignore_comment(self, t):
        r'\#.+'
        pass

    def t_error(self, t):
        raise SyntaxError(t)

    def input(self, data):
        self.lexer.input(data)

'''
metadata : members

members : attr
        | members attr

attr : singular
     | obj

singular : ID = value
         | ID = '[' ']'
         | ID = '[' elements ']'

value : INT
      | FLOAT
      | STRING

elements : value
         | elements ',' value

obj : { }
    | attr { members }
'''

class LVMMetadataParser(object):
    tokens = LVMMetadataLexer.tokens

    def __init__(self):
        self.lexer = LVMMetadataLexer()
        self.parser = yacc.yacc(module=self)

    def p_metadata(self, p):
        '''metadata : members'''
        p[0] = {}
        p[0].update(p[1])

    def p_members(self, p):
        '''members : attr
                   | members attr'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].append(p[2])

    def p_attr(self, p):
        '''attr : singular
                | obj'''
        p[0] = p[1]

    def p_singular(self, p):
        '''singular : ID '=' value
                    | ID '=' '[' ']'
                    | ID '=' '[' elements ']' '''
        if len(p) == 4:
            p[0] = (p[1], p[3])
        elif len(p) == 5:
            p[0] = (p[1], [])
        else:
            p[0] = (p[1], p[4])

    def p_value(self, p):
        '''value : INT
                 | FLOAT
                 | STRING'''
        p[0] = p[1]

    def p_elements(self, p):
        '''elements : value
                    | elements ',' value'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1]
            p[0].append(p[3])


    def p_obj(self, p):
        '''obj : ID '{' '}'
               | ID '{' members '}' '''
        obj = {}
        if len(p) > 4:
            obj.update(p[3])
        p[0] = (p[1], obj)


    def p_error(self, p):
        raise SyntaxError(p)

    def parse(self, text):
        return self.parser.parse(text, self.lexer)


class Metadata(object):
    path = '/etc/lvm/backup'
    mds = {}
    def __init__(self, vgname):
        self.parser = LVMMetadataParser()
        self._data = None
        self.mtime = 0
        self.vgname = vgname
        self.vgpath = '%s/%s' % (self.path,self.vgname)

    def __getitem__(self, name):
        return self.data[name]

    def __iter__(self):
        return iter(self.data)

    @property
    def data(self):
        def preprocess(md, vgname):
            vg = md[vgname]
            pvs = vg['physical_volumes']
            lvs = vg['logical_volumes']
            for n, o in pvs.items():
                o['name'] = n
            for n, o in lvs.items():
                o['name'] = n
            for n, lv in lvs.items():
                lv['segments'] = [lv['segment%s'%(i+1)] for i in range(0, lv['segment_count'])]
            return md

        if self._data is None:
            with open(self.vgpath) as fin:
                md = self.parser.parse(fin.read())
                self._data = preprocess(md, self.vgname)
            self.mtime = os.stat(self.vgpath).st_mtime
            return self._data
        else:
            mtime = os.stat(self.vgpath).st_mtime
            if mtime <> self.mtime:
                self._data = None
                return self.data
            else:
                return self._data

    @property
    def vg(self):
        return self.data[self.vgname]

    def lv_pvs(self, lvname):
        pvs = set(seg['stripes'][0] for seg in self.lv(lvname)['segments'])
        return [self.vg['physical_volumes'][pvname] for pvname in pvs]

    def lv(self, lvname):
        return self.vg['logical_volumes'][lvname]

    @classmethod
    def get(cls, vgname):
        if vgname in cls.mds:
            return cls.mds[vgname]
        else:
            md = Metadata(vgname)
            cls.mds[vgname] = md
            return md

