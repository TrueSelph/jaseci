obj outer {
    has o1: int = 9;

    obj inner {
        has i1: int = 8;
    }
    can foo() {
        return 'foo';
    }
    enum  color {
        red,
        green,
        blue,
        with entry {
            print('Initializing role system..');
        },
        can foo -> str {
            return 'Accessing privileged Data';
        }
    }
}

with entry {
    print(outer.color.green.value, outer.color.foo());
}
