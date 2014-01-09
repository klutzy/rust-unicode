extern mod extra;

use unicode::{general_category, combining_class, uppercase, lowercase, alphabetic};
use unicode::compat_decomp;
use extra::test::BenchHarness;

mod unicode;

#[test]
fn test_general_category_bmp() {
    let values = [
        ('\x00', unicode::Cc),
        ('\x1F', unicode::Cc),
        ('\x20', unicode::Zs),
        ('\x21', unicode::Po),
        ('\x23', unicode::Po),
        ('\x24', unicode::Sc),
        ('\uac00', unicode::Lo), // <Hangul Syllable, First>
        ('\ud7a3', unicode::Lo), // <Hangul Syllable, Last>
        ('\ud7a4', unicode::Cn),
    ];

    for &(v1, v2) in values.iter() {
        let gen_cat = general_category(v1);
        assert_eq!(v2, gen_cat);
    }
}

#[test]
fn test_general_category_others() {
    let values = [
        ('\U0002FA1D', unicode::Lo),
        ('\U000E0000', unicode::Cn),
        ('\U000E0001', unicode::Cf),
        ('\U000E01EF', unicode::Mn),
        ('\U000E01F0', unicode::Cn),
        ('\U000F0000', unicode::Co), // private use area
        ('\U000FFFFD', unicode::Co), // private use area
        ('\U000FFFFE', unicode::Cn),
        ('\U00100000', unicode::Co),
        ('\U0010FFFD', unicode::Co),
        ('\U0010FFFE', unicode::Cn),
    ];

    for &(v1, v2) in values.iter() {
        let gen_cat = general_category(v1);
        assert_eq!(v2, gen_cat);
    }
}

#[bench]
fn bench_general_category_bmp(bh: &mut BenchHarness) {
    let bmp_vals = [
        // just some random values
        '\x00', '\x1F', '\x20', '\x21',
        '\x23', '\x24', '\x61', '\x62',
    ];
    bh.iter(|| {
        for c in bmp_vals.iter() {
            general_category(*c);
        }
    });
}

#[bench]
fn bench_general_category_nonbmp(bh: &mut BenchHarness) {
    let bmp_vals = [
        // yet another random values
        '\U00010000', '\U00010341',
        '\U0001d540', '\U0001d746',
        '\U0002e000', '\U0002fa1d',
        '\U000e0001', '\U000e01c0',
    ];
    bh.iter(|| {
        for c in bmp_vals.iter() {
            general_category(*c);
        }
    });
}

#[test]
fn test_combining_class() {
    let values = [
        ('\x00', 0),
        ('\u0300', 230),
        ('\u0314', 230),
        ('\u0315', 232),
        ('\u0316', 220),
        ('\u0319', 220),
        ('\ufe26', 230),
        ('\ufe26', 230),
        ('\U000101fd', 220),
        ('\U00010a0d', 220),
        ('\U0001d244', 230),
    ];

    for &(v1, v2) in values.iter() {
        let comb = combining_class(v1);
        assert_eq!(v2, comb);
    }
}

#[test]
fn test_uppercase() {
    let uppers = [
        '\x41', // LATIN CAPITAL LETTER A
        '\x5A', // LATIN CAPITAL LETTER Z

        '\xC0', // LATIN CAPITAL LETTER A WITH GRAVE
        '\xD6', // LATIN CAPITAL LETTER O WITH DIAERESIS

        '\u0100', // LATIN CAPITAL LETTER A WITH MACRON
        '\u0102', // LATIN CAPITAL LETTER A WITH BREVE

        '\uA7AA', // LATIN CAPITAL LETTER H WITH HOOK

        '\uFF21', // FULLWIDTH LATIN CAPITAL LETTER A
        '\uFF3A', // FULLWIDTH LATIN CAPITAL LETTER Z

        '\U00010400', // DESERET CAPITAL LETTER LONG I
        '\U00010427', // DESERET CAPITAL LETTER EW

        '\U0001D7CA', // MATHEMATICAL BOLD CAPITAL DIGAMMA
    ];

    for upper in uppers.iter() {
        assert!(uppercase(*upper));
        assert!(!lowercase(*upper));
    }
}

#[test]
fn test_lowercase() {
    let lowers = [
        '\x61', // LATIN SMALL LETTER A
        '\x7A', // LATIN SMALL LETTER Z

        '\xAA', // FEMININE ORDINAL INDICATOR
        '\xB5', // MICRO SIGN
        '\xBA', // MASCULINE ORDINAL INDICATOR

        '\xDF', // LATIN SMALL LETTER SHARP S
        '\xF6', // LATIN SMALL LETTER O WITH DIAERESIS

        '\xF8', // LATIN SMALL LETTER O WITH STROKE
        '\xFF', // LATIN SMALL LETTER Y WITH DIAERESIS

        '\uFF41', // FULLWIDTH LATIN SMALL LETTER A
        '\uFF5A', // FULLWIDTH LATIN SMALL LETTER Z

        '\U00010428', // DESERET SMALL LETTER LONG I
        '\U0001044F', // DESERET SMALL LETTER EW

        '\U0001D7CB', // MATHEMATICAL BOLD CAPITAL DIGAMMA
    ];

    for lower in lowers.iter() {
        assert!(lowercase(*lower));
        assert!(!uppercase(*lower));
    }
}

#[test]
fn test_alphabetic() {
    let alphabets = [
        '\x41', // LATIN CAPITAL LETTER A
        '\x5A', // LATIN CAPITAL LETTER Z

        '\x61', // LATIN SMALL LETTER A
        '\x7A', // LATIN SMALL LETTER Z

        '\xAA', // FEMININE ORDINAL INDICATOR
        '\xB5', // MICRO SIGN
        '\xBA', // MASCULINE ORDINAL INDICATOR

        '\xC0', // LATIN CAPITAL LETTER A WITH GRAVE
        '\xD6', // LATIN CAPITAL LETTER O WITH DIAERESIS

        '\xD8', // LATIN CAPITAL LETTER A WITH GRAVE

        '\xDF', // LATIN SMALL LETTER SHARP S
        '\xF6', // LATIN SMALL LETTER O WITH DIAERESIS

        '\xF8', // LATIN SMALL LETTER O WITH STROKE
        '\xFF', // LATIN SMALL LETTER Y WITH DIAERESIS

        '\u01BB', // LATIN LETTER TWO WITH STROKE

        '\uFFDA', // HALFWIDTH HANGUL LETTER EU
        '\uFFDC', // HALFWIDTH HANGUL LETTER I

        '\U00010000', // LINEAR B SYLLABLE B008 A
        '\U0001000B', // LINEAR B SYLLABLE B046 JE

        '\U0002F800', // CJK COMPATIBILITY IDEOGRAPH-2F800
        '\U0002FA1D', // CJK COMPATIBILITY IDEOGRAPH-2FA1D
    ];

    for alphabet in alphabets.iter() {
        assert!(alphabetic(*alphabet));
    }
}

fn assert_array_eq(a: &[char], b: Option<&[u32]>) {
    let b = b.expect("b should be Some");
    assert_eq!(a.len(), b.len());
    for i in range(0, a.len()) {
        assert_eq!(a[i] as u32, b[i]);
    }
}

#[test]
fn test_compat_decomp_bmp() {
    let answers = [
        // borrowed from std::unicode
        ('\xA0', &['\x20']),
        ('\xa8', &['\x20', '\u0308']),
        ('\xaa', &['\x61']),
        ('\xaf', &['\x20', '\u0304']),
        ('\xb2', &['\x32']),
        ('\xb3', &['\x33']),
        ('\xb4', &['\x20', '\u0301']),
        ('\xb5', &['\u03bc']),
        ('\xb8', &['\x20', '\u0327']),
        ('\xb9', &['\x31']),
        ('\xba', &['\x6f']),

        ('\uffe2', &['\xac']),
        ('\uffe3', &['\xaf']),
        ('\uffe4', &['\xa6']),
        ('\uffe5', &['\xa5']),
        ('\uffe6', &['\u20a9']),
        ('\uffe8', &['\u2502']),
        ('\uffe9', &['\u2190']),
        ('\uffea', &['\u2191']),
        ('\uffeb', &['\u2192']),
        ('\uffec', &['\u2193']),
        ('\uffed', &['\u25a0']),
        ('\uffee', &['\u25cb']),
    ];

    for &(a, bs) in answers.iter() {
        assert_array_eq(bs, compat_decomp(a));
    }
}

#[test]
fn test_compat_decomp_nonbmp() {
    let answers = [
        // borrowed from std::unicode
        ('\U0001d400', &['\x41']), ('\U0001d401', &['\x42']),
        ('\U0001d402', &['\x43']), ('\U0001d403', &['\x44']),
        ('\U0001d404', &['\x45']), ('\U0001d405', &['\x46']),
        ('\U0001d406', &['\x47']), ('\U0001d407', &['\x48']),

        ('\U0001f241', &['\u3014', '\u4e09', '\u3015']),
        ('\U0001f242', &['\u3014', '\u4e8c', '\u3015']),
        ('\U0001f243', &['\u3014', '\u5b89', '\u3015']),
        ('\U0001f244', &['\u3014', '\u70b9', '\u3015']),
        ('\U0001f245', &['\u3014', '\u6253', '\u3015']),
        ('\U0001f246', &['\u3014', '\u76d7', '\u3015']),
        ('\U0001f247', &['\u3014', '\u52dd', '\u3015']),
        ('\U0001f248', &['\u3014', '\u6557', '\u3015']),
        ('\U0001f250', &['\u5f97']),
        ('\U0001f251', &['\u53ef']),
    ];

    for &(a, bs) in answers.iter() {
        assert_array_eq(bs, compat_decomp(a));
    }
}

#[test]
fn test_compat_decomp_none() {
    let vals = [
        // some arbitrary examples...
        '\x00', '\x01', '\xA1', '\xA1',
        '\xA9', '\xAB', '\xB0', '\xB6',
        '\u0903', '\u0B85', '\uFE73', '\uFFE7',
        '\U0002F800', '\U0002F801', '\U0002F802', '\U0002F803',
    ];

    for &val in vals.iter() {
        assert_eq!(None, compat_decomp(val));
    }
}
