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


def fetch(f):
    if not os.path.exists(f):
        os.system("curl -O http://www.unicode.org/Public/UNIDATA/%s"
                  % f)

    if not os.path.exists(f):
        sys.stderr.write("cannot load %s" % f)
        exit(1)


def discontinuous(a, b):
    if a + 1 < b:
        # unassigned area exists
        return True
    return a <= 0xffff and b > 0xffff


def load_unicode_data(f):
    gencats = []
    prev_gencat = "Cn"
    prev_gencat_start = 0
    prev_gencat_end = 0

    combines = []
    prev_combine = 0
    prev_combine_start = 0
    prev_combine_end = 0

    for line in fileinput.input(f):
        fields = line.split(";")
        if len(fields) != 15:
            continue
        [code, name, gencat, combine, bidi,
         decomp, deci, digit, num, mirror,
         old, iso, upcase, lowcase, titlecase] = fields
        code = int(code, 16)

        if prev_gencat != gencat:
            gencats.append((prev_gencat, prev_gencat_start))
            if discontinuous(prev_gencat_end, code):
                gencats.append(("Cn", prev_gencat_end + 1))
            prev_gencat = gencat
            prev_gencat_start = code
            prev_gencat_end = code
        else:
            prev_gencat_end = code

        if prev_combine != combine or discontinuous(prev_combine_end, code):
            if int(prev_combine) != 0:
                combines.append((prev_combine, prev_combine_start,
                                prev_combine_end))
            prev_combine = combine
            prev_combine_start = code
            prev_combine_end = code
        else:
            prev_combine_end = code

    gencats = gencats[1:]

    return {
        'gencats': gencats,
        'combines': combines,
    }


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


def emit_single_table(f, tbl_prefix, tbl, type_name):
    # bmp
    bmp_tbl_name = "{}_bmp_table".format(tbl_prefix)
    f.write("static {}: &'static [(u16, {})] = &[\n"
            .format(bmp_tbl_name, type_name))
    ix = 0
    for cat, lo in tbl:
        if lo > 0xFFFF:
            break
        f.write(ch_prefix(ix, indent=4))
        f.write("(%s, %s)" % (escape_u(lo), cat))
        ix += 1
    f.write("\n];\n\n")

    # other planes. TODO planewise?
    others_tbl_name = "{}_others_table".format(tbl_prefix)
    f.write("static {}: &'static [(u32, {})] = &[\n"
            .format(others_tbl_name, type_name))
    ix = 0
    for cat, lo in tbl:
        if lo <= 0xFFFF:
            continue
        f.write(ch_prefix(ix, indent=4))
        f.write("(%s, %s)" % (escape_u(lo), cat))
        ix += 1
    f.write("\n];\n\n")

    f.write("pub fn {}(c: char) -> {} {{".format(tbl_prefix, type_name))
    f.write("""
    let c = c as u32;
    if c <= 0xffff {
        let v = bsearch_range(%s, |&(lo, _), &(hi, _)| {
            let c = c as u16;
            if lo <= c && c < hi { Equal }
            else if hi <= c { Less }
            else { Greater }
        });
        let idx = v.unwrap();
        let (_, val) = %s[idx];
        return val;
    } else {
        let v = bsearch_range(%s, |&(lo, _), &(hi, _)| {
            if lo <= c && c < hi { Equal }
            else if hi <= c { Less }
            else { Greater }
        });
        let idx = v.unwrap();
        let (_, val) = %s[idx];
        return val;
    };
}
""" % (bmp_tbl_name, bmp_tbl_name, others_tbl_name, others_tbl_name))


def emit_range_table(f, tbl_prefix, tbl, type_name, default='0'):
    # XXX mostly dup of emit_single_table
    # assumes lo and hi are EITHER both in bmp OR both not in bmp.
    # bmp
    bmp_tbl_name = "{}_bmp_table".format(tbl_prefix)
    f.write("static {}: &'static [(u16, u16, {})] = &[\n"
            .format(bmp_tbl_name, type_name))
    ix = 0
    for cat, lo, hi in tbl:
        if lo > 0xFFFF:
            break
        f.write(ch_prefix(ix, indent=4))
        f.write("(%s, %s, %s)" % (escape_u(lo), escape_u(hi), cat))
        ix += 1
    f.write("\n];\n\n")

    # other planes. TODO planewise?
    others_tbl_name = "{}_others_table".format(tbl_prefix)
    f.write("static {}: &'static [(u32, u32, {})] = &[\n"
            .format(others_tbl_name, type_name))
    ix = 0
    for cat, lo, hi in tbl:
        if lo <= 0xFFFF:
            continue
        f.write(ch_prefix(ix, indent=4, linebreak=2))
        f.write("(%s, %s, %s)" % (escape_u(lo), escape_u(hi), cat))
        ix += 1
    f.write("\n];\n\n")

    f.write("pub fn {}(c: char) -> {} {{".format(tbl_prefix, type_name))
    f.write("""
    let c = c as u32;
    if c <= 0xffff {
        let idx = %s.bsearch(|&(lo, hi, _)| {
            let c = c as u16;
            if lo <= c && c <= hi { Equal }
            else if hi < c { Less }
            else { Greater }
        });
        match idx {
            Some(idx) => {
                let (_, _, val) = %s[idx];
                return val;
            }
            None => {
                return %s;
            }
        }
    } else {
        let idx = %s.bsearch(|&(lo, hi, _)| {
            if lo <= c && c <= hi { Equal }
            else if hi < c { Less }
            else { Greater }
        });
        match idx {
            Some(idx) => {
                let (_, _, val) = %s[idx];
                return val;
            }
            None => {
                return %s;
            }
        }
    };
}
""" % (bmp_tbl_name, bmp_tbl_name, default,
        others_tbl_name, others_tbl_name, default))


def main():
    r = "unicode.rs"
    for i in [r]:
        if os.path.exists(i):
            os.remove(i)
    rf = open(r, "w")

    f = "UnicodeData.txt"
    #fetch(f)
    data = load_unicode_data(f)

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

fn bsearch_range<T>(table: &[T], f: |&T, &T| -> Ordering) -> Option<uint> {
    let mut base: uint = 0;
    let mut lim: uint = table.len() - 1;

    while lim != 0 {
        let ix = base + (lim >> 1);
        let v = f(&table[ix], &table[ix + 1]);
        match v {
            Equal => return Some(ix),
            Less => {
                base = ix + 1;
                lim -= 1;
            }
            Greater => ()
        }
        lim >>= 1;
    }
    return None;
}

'''.lstrip())

    gen_cat_enum = GEN_CATS
    gen_cat_enum_name = "GeneralCategory"
    gen_cat_tbl_prefix = "general_category"
    emit_enum(rf, gen_cat_enum, gen_cat_enum_name, indent=0)
    emit_single_table(rf, gen_cat_tbl_prefix, data['gencats'],
                      gen_cat_enum_name)

    rf.write('\n')

    combine_tbl_prefix = "combining_class"
    emit_range_table(rf, combine_tbl_prefix, data['combines'], "u8")


if __name__ == '__main__':
    main()
