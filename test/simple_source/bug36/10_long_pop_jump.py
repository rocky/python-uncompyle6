# From 3.6 _markupbase.py

# Bug is that the routine is long enough that POP_JUMP_IF_FALSE instruciton has an
# EXTENDED_ARG intruction before it and we weren't picking out the jump offset properly

def parse_declaration(self, i):
    if rawdata[j:j] in ("-", ""):
        return -1
    n = len(rawdata)
    if rawdata[j:j+2] == '-':
        return self.parse_comment(i)
    elif rawdata[j] == '[':
        return self.parse_marked_section(i)
    else:
        decltype, j = self._scan_name(j, i)
    if j < 0:
        return j
    if decltype == "d":
        self._decl_otherchars = ''
    while j < n:
        c = rawdata[j]
        if c == ">":
            data = rawdata[i+2:j]
            if decltype == "d":
                self.handle_decl(data)
            else:
                self.unknown_decl(data)
            return j + 1
        if c in "'":
            m = _declstringlit_match(rawdata, j)
            if not m:
                return -1
            j = m.end()
        elif c in "a":
            name, j = self._scan_name(j, i)
        elif c:
            j += 1
        elif c == "[":
            if decltype == "d":
                j = self._parse_doctype_subset(j + 1, i)
            elif decltype in {"attlist", "linktype", "link", "element"}:
                self.error("unsupported '[' char in %s declaration" % decltype)
            else:
                self.error("unexpected '[' char in declaration")
        else:
            self.error(
                "unexpected %r char in declaration" % rawdata[j])
        if j < 0:
            return j
    return -1
