import:jac from bar { bar_walk }
import:py from jaclang.runtimelib.feature { JacFeature, JacMachineState }
import:py os;

can update_bar_walker {
    "Updating bar.jac with new behavior." |> print;
    (bar_walk_new, ) = JacFeature.update_walker(JacFeature.py_get_jac_machine(),
        "bar",
        items={'bar_walk': None}
    );
    "Running bar_walk after update..." |> print;
    root spawn bar_walk_new();
    print(f"bar_walk: {bar_walk_new.__dict__}");
}


with entry {
    update_bar_walker();
}