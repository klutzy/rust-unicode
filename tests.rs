extern mod extra;

use unicode::{general_category, combining_class, uppercase, lowercase, alphabetic};
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
