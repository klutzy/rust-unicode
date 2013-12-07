extern mod extra;

use unicode::general_category;
use extra::test::BenchHarness;

mod unicode;

#[test]
fn test_general_category() {
    let values = [
        ('\x00', unicode::Cc),
        ('\x1F', unicode::Cc),
        ('\x20', unicode::Zs),
        ('\x21', unicode::Po),
        ('\x23', unicode::Po),
        ('\x24', unicode::Sc),
        ('\U0002FA1D', unicode::Lo),
        ('\U000E0000', unicode::Cn),
        ('\U000E0001', unicode::Cf),
    ];

    for &(v1, v2) in values.iter() {
        let gen_cat = general_category(v1);
        println!("v2: {:?} / gen_cat: {:?}", v2, gen_cat);
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

//fn is_alphanumeric(c: char) -> bool {
//
//}
//
//#[bench]
//fn bench_is_alphanumeric(bh: &BenchHarness) {
//}
