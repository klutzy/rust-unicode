#!/usr/bin/env python
# xfail-license

# This digests UnicodeData.txt and DerivedCoreProperties.txt and emits rust
# code covering the core properties. Since this is a pretty rare event we
# just store this out-of-line and check the unicode.rs file into git.
#
# The emitted code is "the minimum we think is necessary for libstd", that
# is, to support basic operations of the compiler and "most nontrivial rust
# programs". It is not meant to be a complete implementation of unicode.
# For that we recommend you use a proper binding to libicu.

import fileinput
import os
import sys
import re


def write_str_list(f, strs, name, nl=8, spaces=4):
    f.write("static {}: &'static [&'static str] = &[\n".format(name))
    f.write(" " * spaces)
    for i, s in enumerate(strs):
        f.write("\"" + s + "\",")
        if i == len(strs) - 1:
            f.write("\n")
        elif i % nl == nl - 1:
            f.write("\n")
            f.write(" " * spaces)
        else:
            f.write(" ")
    f.write("];\n\n")


def emit_enum(f, strs, name, nl=8, indent=4):
    f.write((" " * indent) + "#[deriving(Eq)]\n")
    f.write((" " * indent) + "pub enum " + name + " {\n")
    for i, s in enumerate(strs):
        f.write(ch_prefix(i, indent + 4))
        f.write(s)
    f.write("\n" + (" " * indent) + "}\n\n")


# http://www.unicode.org/reports/tr44/#General_Category_Values
GEN_CATS = [
    "Lu", "Ll", "Lt",
    "Lm", "Lo",
    "Mn", "Mc", "Me",
    "Nd", "Nl", "No",
    "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po",
    "Sm", "Sc", "Sk", "So",
    "Zs", "Zl", "Zp",
    "Cc", "Cf", "Cs", "Co",
    "Cn",  # Unassigned
]


def fetch(f, url):
    print f, url
    if not os.path.exists(f):
        os.system("curl -o '{}' '{}'".format(f, url))

    if not os.path.exists(f):
        sys.stderr.write("cannot load %s" % f)
        exit(1)

    return fileinput.input(f)


def fetch_unicode(f, version=None):
    url = "http://www.unicode.org/Public/UNIDATA/{}.txt".format(f)  # latest
    if version:
        if version == "3.2.0":  # < 4.1.0
            url = "http://www.unicode.org/Public/3.2-Update/{}-{}.txt"
            url = url.format(f, version)
            f = "{}-{}.txt".format(f, version)
        else:
            url = "http://www.unicode.org/Public/{}/ucd/{}.txt"
            url = url.format(version, f)
        f = "{}-{}.txt".format(f, version)
    else:
        f = f + ".txt"

    return fetch(f, url)


def fetch_rfc(f):
    return fetch(f, "http://tools.ietf.org/rfc/" + f)


def discontinuous(a, b, a_name, b_name):
    if not a_name:
        return True
    if a_name.endswith('First>') and b_name.endswith('Last>'):
        # start ~ end. Here not (a <= 0xffff and b > 0xffff) is assumed
        return False
    if a + 1 < b:
        # unassigned area exists
        return True
    return a <= 0xffff and b > 0xffff


def load_unicode_data(f):
    gencats = []
    prev_gencat = None
    prev_gencat_start = -1

    combines = []
    prev_combine = -1
    prev_combine_start = -1
    prev_combine_end = -1
    prev_name = None

    canon_decomp = []
    compat_decomp = []

    prev_code = -1

    for line in f:
        fields = line.split(";")
        if len(fields) != 15:
            continue
        [code, name, gencat, combine, bidi,
         decomp, deci, digit, num, mirror,
         old, iso, upcase, lowcase, titlecase] = fields
        code = int(code, 16)

        is_disc = discontinuous(prev_code, code, prev_name, name)

        cn_cat = None
        if is_disc:
            cn_cat = ("Cn", prev_code + 1)

        if prev_gencat != gencat or is_disc:
            gencats.append((prev_gencat, prev_gencat_start))
            prev_gencat = gencat
            prev_gencat_start = code

        if cn_cat:
            gencats.append(cn_cat)

        if prev_combine != combine or \
                discontinuous(prev_combine_end, code, prev_name, name):

            combines.append((prev_combine, prev_combine_start,
                            prev_combine_end))
            prev_combine = combine
            prev_combine_start = code

        if decomp:
            if decomp.startswith('<'):
                seq = []
                for i in decomp.split()[1:]:
                    seq.append(int(i, 16))
                compat_decomp.append((code, seq))
            else:
                seq = []
                for i in decomp.split():
                    seq.append(int(i, 16))
                canon_decomp.append((code, seq))

        prev_combine_end = code
        prev_name = name
        prev_code = code

    gencats.append((prev_gencat, prev_gencat_start))
    gencats.append(("Cn", prev_code + 1))

    gencats = gencats[1:]
    combines = combines[1:]

    return {
        'gencats': gencats,
        'combines': combines,
        'canon_decomp': canon_decomp,
        'compat_decomp': compat_decomp,
    }


def load_properties(f, interestingprops):
    props = {}
    re1 = re.compile("^([0-9A-F]+) +; (\w+)")
    re2 = re.compile("^([0-9A-F]+)\.\.([0-9A-F]+) +; (\w+)")

    for line in f:
        prop = None
        d_lo = 0
        d_hi = 0
        m = re1.match(line)
        if m:
            d_lo = m.group(1)
            d_hi = m.group(1)
            prop = m.group(2)
        else:
            m = re2.match(line)
            if m:
                d_lo = m.group(1)
                d_hi = m.group(2)
                prop = m.group(3)
            else:
                continue
        if prop not in interestingprops:
            continue
        d_lo = int(d_lo, 16)
        d_hi = int(d_hi, 16)
        if prop not in props:
            props[prop] = []
        props[prop].append((d_lo, d_hi))
    return props


def load_stringprep(f):
    tbls = [
        # ranges
        'A.1',  # Unassigned code points in Unicode 3.2

        # mappings
        'B.1',  # Commonly mapped to nothing
        'B.2',  # Mapping for case-folding used with NFKC
        'B.3',  # Mapping for case-folding used with no normalization

        # ranges
        'C.1.1',  # ASCII space characters
        'C.1.2',  # Non-ASCII space characters
        'C.2.1',  # ASCII control characters
        'C.2.2',  # Non-ASCII control characters

        # ranges
        'C.3',  # Private use
        'C.4',  # Non-character code points
        'C.5',  # Surrogate codes
        'C.6',  # Inappropriate for plain text
        'C.7',  # Inappropriate for canonical representation
        'C.8',  # Change display properties or are deprecated
        'C.9',  # Tagging characters

        # ranges
        'D.1',  # Characters with bidirectional property "R" or "AL"
        'D.2',  # Characters with bidirectional property "L"
    ]

    result = {}
    for key in tbls:
        result[key] = []

    cur_tbl = None

    for line in f:
        if not line.startswith(" " * 3):
            continue
        line = line.strip()
        if line.startswith("-----") and line.endswith("-----"):
            _, ind, _tab, section, _ = line.split()
            assert _tab == "Table"
            if ind == "Start":
                assert cur_tbl is None
                cur_tbl = section
            else:
                assert ind == "End"
                assert cur_tbl == section
                cur_tbl = None
        elif cur_tbl:
            vals = line.split(';')
            if cur_tbl[0] == 'B':
                # mappings
                map_from, map_to, _ = vals
                map_from = int(map_from, 16)
                map_to = [int(i, 16) for i in map_to.split()]
                result[cur_tbl].append((map_from, map_to))
            else:
                r = vals[0].split('-')
                assert len(r) in (1, 2)
                start = int(r[0], 16)
                end = start
                if len(r) == 2:
                    end = int(r[1], 16)
                result[cur_tbl].append((start, end))

    return result


def escape_u(c):
    if c <= 0xff:
        return "0x%2.2x" % c
    if c <= 0xffff:
        return "0x%4.4x" % c
    return "0x%8.8x" % c


def escape_char(c):
    if c <= 0xff:
        return "'\\x%2.2x'" % c
    if c <= 0xffff:
        return "'\\u%4.4x'" % c
    return "'\\U%8.8x'" % c


def ch_prefix(ix, indent=8, linebreak=4):
    if ix == 0:
        return " " * indent
    if ix % linebreak == 0:
        return ",\n" + (" " * indent)
    else:
        return ", "


def emit_bsearch_range_table(f):
    f.write("""
    fn bsearch_range_table(c: char, r: &'static [(char,char)]) -> bool {
        use cmp::{Equal, Less, Greater};
        use vec::ImmutableVector;
        use option::None;
        r.bsearch(|&(lo,hi)| {
            if lo <= c && c <= hi { Equal }
            else if hi < c { Less }
            else { Greater }
        }) != None
    }\n\n
""")


def emit_table(f, tbl_name, elem_type, is_range, tbl, lb=4):
    f.write("static {}: &'static [{}] = &[\n"
            .format(tbl_name, elem_type))
    ix = 0
    for vals in tbl:
        lo = None
        hi = None
        elems = None
        if is_range:
            lo = escape_u(vals[-2])
            hi = escape_u(vals[-1])
            elems = [lo, hi] + list(vals[:-2])
        else:
            lo = escape_u(vals[-1])
            elems = [lo, ] + list(vals[:-1])

        f.write(ch_prefix(ix, indent=4, linebreak=lb))
        f.write("(" + ", ".join(str(i) for i in elems) + ")")
        ix += 1
    f.write("\n];\n\n")


def emit_single_table(f, tbl_prefix, tbl, type_name):
    nidx = 0
    for i, x in enumerate(tbl):
        nidx = i
        if x[-1] > 0xFFFF:
            break

    # bmp
    bmp_tbl_name = "{}_bmp_table".format(tbl_prefix)
    elem_type = "(u16, {})".format(type_name)
    emit_table(f, bmp_tbl_name, elem_type, False, tbl[:nidx])

    # other planes. TODO planewise?
    others_tbl_name = "{}_others_table".format(tbl_prefix)
    elem_type = "(u32, {})".format(type_name)
    emit_table(f, others_tbl_name, elem_type, False, tbl[nidx:])

    bsearch = """
        let idx = bsearch_range(%s, |&(lo, _), &(hi, _)| {
            if lo <= c && c < hi { Equal }
            else if hi <= c { Less }
            else { Greater }
        });
        let (_, val) = %s[idx];
        return val;"""

    f.write("pub fn {}(c: char) -> {} {{".format(tbl_prefix, type_name))
    f.write("""
    let c = c as u32;
    if c <= 0xffff {
        let c = c as u16;
%s
    } else {
%s
    };
}

""" % (bsearch % (bmp_tbl_name, bmp_tbl_name),
        bsearch % (others_tbl_name, others_tbl_name)))


def emit_range_table(f, tbl_prefix, tbl, type_name=None, default='0'):
    nidx = 0
    for i, x in enumerate(tbl):
        nidx = i
        if x[-1] > 0xFFFF:
            break

    # bmp
    bmp_type = "(u16, u16, {})".format(type_name)
    if not type_name:
        bmp_type = "(u16, u16)"
    bmp_tbl_name = "{}_bmp_table".format(tbl_prefix)
    emit_table(f, bmp_tbl_name, bmp_type, True, tbl[:nidx])

    # other planes. TODO planewise? bitmap?
    others_type = "(u32, u32, {})".format(type_name)
    if not type_name:
        others_type = "(u32, u32)"
    others_tbl_name = "{}_others_table".format(tbl_prefix)
    emit_table(f, others_tbl_name, others_type, True, tbl[nidx:], lb=2)

    bsearch = """
        let idx = %(tbl_name)s.bsearch(|&%(elem_type)s| {
            if lo <= c && c <= hi { Equal }
            else if hi < c { Less }
            else { Greater }
        });"""

    elem_type = "(lo, hi, _)"
    if not type_name:
        elem_type = "(lo, hi)"

    if type_name:
        f.write("pub fn {}(c: char) -> {} {{".format(tbl_prefix, type_name))
        bsearch += """
        match idx {
            Some(idx) => {
                let (_, _, val) = %(tbl_name)s[idx];
                return val;
            }
            None => {
                return %(def_val)s;
            }
        }"""
    else:
        f.write("pub fn {}(c: char) -> bool {{".format(tbl_prefix))
        bsearch += """
        return idx.is_some();"""

    bsearch_blobs = []
    for tbl_name in (bmp_tbl_name, others_tbl_name):
        bsearch_blobs.append(bsearch % {
            'tbl_name': tbl_name,
            'def_val': default,
            'elem_type': elem_type
        })

    f.write("""
    let c = c as u32;
    if c <= 0xffff {
        let c = c as u16;
%s
    } else {%s
    };
}

""" % (bsearch_blobs[0], bsearch_blobs[1]))


def main():
    r = "unicode.rs"
    for i in [r]:
        if os.path.exists(i):
            os.remove(i)
    rf = open(r, "w")

    unicode_version = "6.3.0"

    data = fetch_unicode("UnicodeData", unicode_version)
    data = load_unicode_data(data)

    # Preamble
    rf.write('''
// Copyright 2012-2013 The Rust Project Developers. See the COPYRIGHT
// file at the top-level directory of this distribution and at
// http://rust-lang.org/COPYRIGHT.
//
// Licensed under the Apache License, Version 2.0 <LICENSE-APACHE or
// http://www.apache.org/licenses/LICENSE-2.0> or the MIT license
// <LICENSE-MIT or http://opensource.org/licenses/MIT>, at your
// option. This file may not be copied, modified, or distributed
// except according to those terms.

// The following code was generated by "src/etc/unicode.py"

#[allow(missing_doc)];
#[allow(non_uppercase_statics)];
use std::cmp::{Equal, Less, Greater};

fn bsearch_range<T>(table: &[T], f: |&T, &T| -> Ordering) -> uint {
    let mut base: uint = 0;
    let len = table.len();
    let mut lim: uint = len - 1;

    while lim != 0 {
        let ix = base + (lim >> 1);
        let v = f(&table[ix], &table[ix + 1]);
        match v {
            Equal => return ix,
            Less => {
                base = ix + 1;
                lim -= 1;
            }
            Greater => ()
        }
        lim >>= 1;
    }
    return len - 1;
}

'''.lstrip())

    gen_cat_enum = GEN_CATS
    gen_cat_enum_name = "GeneralCategory"
    emit_enum(rf, gen_cat_enum, gen_cat_enum_name, indent=0)
    emit_single_table(rf, "general_category", data['gencats'],
                      gen_cat_enum_name)

    rf.write('\n')

    emit_range_table(rf, "combining_class", data['combines'], "u8")

    derived = fetch_unicode("DerivedCoreProperties", unicode_version)
    derived = load_properties(derived, [
        # "XID_Start", "XID_Continue",
        "Alphabetic", "Lowercase", "Uppercase"
    ])

    for prop in derived:
        emit_range_table(rf, prop.lower(), derived[prop])

    stringprep = fetch_rfc("rfc3454.txt")
    stringprep = load_stringprep(stringprep)

    for k in sorted(stringprep.keys()):
        print("{}: {} entries".format(k, len(stringprep[k])))


if __name__ == '__main__':
    main()
