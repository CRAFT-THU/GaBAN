use std::{
    cell::{Ref, RefCell, RefMut},
    collections::HashSet,
    fs::File,
    io::{BufRead, BufReader},
    path::PathBuf,
};
use std::{collections::HashMap, fmt::Write};

#[derive(Copy, Clone, PartialEq, Eq, Hash, PartialOrd, Ord, Debug)]
pub struct InstRef(usize);

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
#[repr(transparent)]
pub struct SafeF32(u32);

impl SafeF32 {
    pub fn new(mut val: f32) -> SafeF32 {
        if val.is_nan() {
            val = f32::NAN;
        }
        SafeF32(val.to_bits())
    }
    pub fn set(&mut self, mut val: f32) {
        if val.is_nan() {
            val = f32::NAN;
        }
        self.0 = val.to_bits()
    }
    pub fn get(&self) -> f32 {
        f32::from_bits(self.0)
    }
}

#[derive(Debug, Clone, Hash, PartialEq, Eq)]
pub enum Literal {
    Integer(i32),
    Float(SafeF32),
}
#[derive(Debug, Clone, Hash, PartialEq, Eq)]
pub enum Value {
    // Literal
    Literal(Literal),
    // Temporary
    Inst(InstRef),
    // Input, Variable, Output, Constant
    Variable(String),
}

#[derive(Debug, Clone)]
pub struct Inst {
    // linked list
    prev: Option<InstRef>,
    next: Option<InstRef>,

    lhs: String,
    op: String,
    args: Vec<Value>,
    // used by
    use_set: Vec<InstRef>,
}

pub struct Program {
    insts: Vec<RefCell<Inst>>,
    // insts linked list
    head: RefCell<Option<InstRef>>,
    tail: RefCell<Option<InstRef>>,
    // lhs -> insts, temporary only
    reg_map: HashMap<String, InstRef>,
}

impl Program {
    fn remove_inst(&self, r: InstRef) {
        let inst = self.get_inst(r);

        // linked list update
        let prev = inst.prev;
        let next = inst.next;
        if let Some(next) = self.get_inst(r).next {
            self.get_inst_mut(next).prev = prev;
        }
        if let Some(prev) = self.get_inst(r).prev {
            self.get_inst_mut(prev).next = next;
        }
        drop(inst);

        let mut head = self.head.borrow_mut();
        if Some(r) == *head {
            *head = next;
        }
        let mut tail = self.tail.borrow_mut();
        if Some(r) == *tail {
            *tail = prev;
        }
    }

    fn get_inst(&self, r: InstRef) -> Ref<Inst> {
        self.insts[r.0].borrow()
    }

    fn get_inst_mut(&self, r: InstRef) -> RefMut<Inst> {
        self.insts[r.0].borrow_mut()
    }

    fn insert_tail(&mut self, inst: Inst) -> InstRef {
        assert!(inst.prev.is_none());
        assert!(inst.next.is_none());

        let r = InstRef(self.insts.len());
        self.insts.push(RefCell::new(inst));
        let mut tail_ref = self.tail.borrow_mut();
        if let Some(tail) = *tail_ref {
            self.get_inst_mut(tail).next = Some(r);
            self.get_inst_mut(r).prev = Some(tail);

            *tail_ref = Some(r);
            let mut head = self.head.borrow_mut();
            if head.is_none() {
                *head = Some(r);
            }
        } else {
            *self.head.borrow_mut() = Some(r);
            *tail_ref = Some(r);
        }

        r
    }

    fn insert_head(&mut self, inst: Inst) -> InstRef {
        assert!(inst.prev.is_none());
        assert!(inst.next.is_none());

        let r = InstRef(self.insts.len());
        self.insts.push(RefCell::new(inst));
        let mut head_ref = self.head.borrow_mut();
        if let Some(head) = *head_ref {
            self.get_inst_mut(head).prev = Some(r);
            self.get_inst_mut(r).next = Some(head);

            *head_ref = Some(r);
            let mut tail = self.tail.borrow_mut();
            if tail.is_none() {
                *tail = Some(r);
            }
        } else {
            *self.tail.borrow_mut() = Some(r);
            *head_ref = Some(r);
        }

        r
    }

    pub fn new() -> Self {
        Program {
            insts: vec![],
            head: RefCell::new(None),
            tail: RefCell::new(None),
            reg_map: HashMap::new(),
        }
    }

    pub fn dump(&self) -> String {
        let mut res = String::new();
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let inst = self.get_inst(node);
            write!(res, "{} = {}(", inst.lhs, inst.op).unwrap();
            for (idx, val) in inst.args.iter().enumerate() {
                if idx != 0 {
                    write!(res, ", ").unwrap();
                }
                match val {
                    Value::Literal(num) => match &num {
                        Literal::Integer(i) => write!(res, "{}", i).unwrap(),
                        Literal::Float(_) => {
                            panic!("No floating literal should exist after transformation")
                        }
                    },
                    Value::Variable(name) => write!(res, "{}", name).unwrap(),
                    Value::Inst(i) => write!(res, "{}", self.get_inst(*i).lhs).unwrap(),
                }
            }
            writeln!(res, ")").unwrap();
            node_opt = inst.next;
        }
        res
    }

    pub fn parse(&mut self, path: PathBuf) -> anyhow::Result<()> {
        let file = File::open(path)?;
        for line in BufReader::new(file).lines() {
            let line = line?;
            let parts: Vec<&str> = line.split("=").collect();
            assert_eq!(parts.len(), 2, "Wrong format of ssa!");

            let lhs = parts[0].trim();
            let rhs = parts[1].trim();

            let parts: Vec<&str> = rhs.split("(").collect();
            assert_eq!(parts.len(), 2, "Wrong format of ssa!");
            let op = parts[0].trim();
            let args: Vec<&str> = parts[1]
                .trim_end_matches(")")
                .split(",")
                .map(|s| s.trim())
                .collect();
            let inst = self.insert_tail(Inst {
                prev: None,
                next: None,
                lhs: lhs.to_string(),
                op: op.to_string(),
                args: args
                    .iter()
                    .map(|arg| -> anyhow::Result<Value> {
                        if arg.chars().next().unwrap().is_numeric() {
                            if let Ok(i) = str::parse::<i32>(arg) {
                                Ok(Value::Literal(Literal::Integer(i)))
                            } else if let Ok(f) = str::parse::<f32>(arg) {
                                Ok(Value::Literal(Literal::Float(SafeF32::new(f))))
                            } else {
                                Err(anyhow::anyhow!("Invalid literal"))
                            }
                        } else {
                            if arg.starts_with("T_") {
                                Ok(Value::Inst(
                                    self.reg_map
                                        .get(&arg.to_string())
                                        .expect("Temporary used before definition")
                                        .clone(),
                                ))
                            } else {
                                Ok(Value::Variable(arg.to_string()))
                            }
                        }
                    })
                    .collect::<anyhow::Result<Vec<_>>>()?,
                use_set: vec![],
            });

            if lhs.starts_with("T_") {
                // temporary
                self.reg_map.insert(lhs.to_string(), inst);
            }
        }
        Ok(())
    }

    pub fn analyze(&mut self) {
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let mut inst = self.get_inst_mut(node);
            inst.use_set.clear();
            node_opt = inst.next;
        }

        // calculate use_set
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let inst = self.get_inst(node);
            for val in &inst.args {
                if let Value::Inst(i) = val {
                    self.get_inst_mut(*i).use_set.push(node);
                }
            }
            node_opt = inst.next;
        }
    }

    // match expression simplification
    fn math(&mut self) {
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let inst = self.get_inst(node);
            let next = inst.next;

            // optimize:
            // B = mul_f(1.0, A)
            // to
            // B = move(A)
            if inst.op == "mul_f"
                && inst.args[0] == Value::Literal(Literal::Float(SafeF32::new(1.0)))
            {
                drop(inst);
                let mut inst_mut = self.get_inst_mut(node);
                inst_mut.op = "move".to_string();
                inst_mut.args.remove(0);
            }
            node_opt = next;
        }

        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let inst = self.get_inst(node);
            let next = inst.next;

            // optimize:
            // r3 = muladd_f(r1, 1.0, r2)
            // to:
            // r3 = add_f(r1, r2)
            if inst.op == "muladd_f"
                && inst.args[1] == Value::Literal(Literal::Float(SafeF32::new(1.0)))
            {
                drop(inst);
                let mut inst_mut = self.get_inst_mut(node);
                inst_mut.op = "add_f".to_string();
                inst_mut.args.remove(1);
            }

            node_opt = next;
        }

        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let inst = self.get_inst(node);
            let next = inst.next;

            // Optimization:
            // r1 = div_f(r2, imm)
            // to:
            // r1 = mul_f(r2, 1/imm)
            if inst.op == "div_f" {
                assert_eq!(inst.args.len(), 2);
                drop(inst);
                let mut inst_mut = self.get_inst_mut(node);
                if let Value::Literal(lit) = &mut inst_mut.args[1] {
                    if let Literal::Float(f) = lit {
                        eprintln!("Floating literal division optimisation");
                        *lit = Literal::Float(SafeF32::new(1.0 / f.get()));
                        inst_mut.op = "mul_f".to_string();
                    }
                }
            }

            node_opt = next;
        }
    }

    // dead code elimination
    fn dce(&mut self) {
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let inst = self.get_inst(node);
            let next = inst.next;

            if inst.use_set.len() == 0 && inst.lhs.starts_with("T_") {
                self.remove_inst(node);
            }
            node_opt = next;
        }
    }

    // FMA optimization
    fn fma(&mut self) {
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let inst = self.get_inst(node);
            let next = inst.next;

            // Optimization:
            // merge mul and add/sub
            // v2 = mul_f(v0, v1)
            // v4 = add_f(v2, v3)
            // or
            // v4 = add_f(v3, v2)
            // v2 has only one use
            // merge to:
            // v4 = muladd_f(v0, v1, v3)
            if inst.op == "mul_f" && inst.use_set.len() == 1 {
                let user_ref = &inst.use_set[0];
                let mut user = self.get_inst_mut(*user_ref);
                if user.op == "add_f" || user.op == "sub_f" {
                    let mut update = false;

                    if let Value::Inst(i) = &user.args[0] {
                        if *i == node {
                            update = true;
                            // v4 = add_f(v2, v3)
                            // v4 = sub_f(v2, v3)
                            user.args = vec![
                                inst.args[0].clone(),
                                inst.args[1].clone(),
                                user.args[1].clone(),
                            ];
                        }
                    }
                    if let Value::Inst(i) = &user.args[1] {
                        if *i == node && user.op == "add_f" {
                            update = true;
                            // v4 = add_f(v3, v2)
                            user.args = vec![
                                inst.args[0].clone(),
                                inst.args[1].clone(),
                                user.args[0].clone(),
                            ];
                        }
                    }

                    if update {
                        eprintln!("FMA optimization");
                        // replace user
                        user.op = if user.op == "add_f" {
                            "muladd_f".to_string()
                        } else {
                            "mulsub_f".to_string()
                        };

                        // replace use set of v0 and v1
                        for arg in &inst.args {
                            if let Value::Inst(i_ref) = arg {
                                let mut i = self.get_inst_mut(*i_ref);
                                for u in &mut i.use_set {
                                    if *u == node {
                                        *u = *user_ref;
                                    }
                                }
                            }
                        }

                        // avoid double borrow mut
                        drop(user);

                        // remove current inst
                        self.remove_inst(node);
                    }
                }
            }
            node_opt = next;
        }
    }

    // peephole optimization
    fn peephole(&mut self) {
        // move optimization
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let inst = self.get_inst(node);
            let next = inst.next;

            // Optimization:
            // r3 = op(r1, r2)
            // V_r3 = move(r3)
            // and r3 has only one use
            // merge to:
            // V_r3 = op(r1, r2)
            if inst.use_set.len() == 1 {
                let user_ref = inst.use_set[0].clone();
                let user = self.get_inst_mut(user_ref);
                if user.op == "move" {
                    // remove user
                    eprintln!("Move optimization");
                    let lhs = user.lhs.clone();
                    drop(inst);
                    drop(user);
                    self.remove_inst(user_ref);

                    // replace inst lhs
                    let mut inst = self.get_inst_mut(node);
                    inst.lhs = lhs;
                    inst.use_set.clear();
                }
            }

            node_opt = next;
        }

        // move optimization
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let inst = self.get_inst(node);
            let next = inst.next;

            // Optimization:
            // T_r2 = move(r1)
            // replace all use of T_r2 with r1
            // and remove the `move` instruction
            if inst.op == "move" && inst.lhs.starts_with("T_") {
                eprintln!("Move optimization");
                let rhs = inst.args[0].clone();
                for user_ref in inst.use_set.clone() {
                    let mut user = self.get_inst_mut(user_ref);
                    for arg in user.args.iter_mut() {
                        if *arg == Value::Inst(node) {
                            *arg = rhs.clone();
                        }
                    }
                }

                self.remove_inst(node);
            }

            node_opt = next;
        }
    }

    fn cse(&mut self) {
        // common subexpression elimination
        // collect ops -> inst
        // and replace
        let mut map: HashMap<(String, Vec<Value>), InstRef> = HashMap::new();
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let inst = self.get_inst(node);
            let next = inst.next;

            let key = (inst.op.clone(), inst.args.clone());
            if map.contains_key(&key) && inst.lhs.starts_with("T_") {
                eprintln!("CSE optimization");
                let prev_inst_ref = map[&key];
                let mut prev_inst = self.get_inst_mut(prev_inst_ref);
                if prev_inst.lhs.starts_with("T_") {
                    for user_ref in &inst.use_set {
                        let mut user = self.get_inst_mut(*user_ref);
                        for arg in &mut user.args {
                            if let Value::Inst(i) = arg {
                                if *i == node {
                                    // replace all uses with prev inst
                                    *i = prev_inst_ref;
                                    prev_inst.use_set.push(*user_ref);
                                }
                            }
                        }
                    }
                }

                // avoid double borrow
                drop(inst);
                drop(prev_inst);
                self.remove_inst(node);
            } else {
                map.insert(key, node);
            }

            node_opt = next;
        }
    }

    pub fn lower(&mut self) {
        // map: f32 -> imm loaded
        let mut float_map: HashMap<SafeF32, InstRef> = HashMap::new();
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let next = self.get_inst(node).next;

            // handle floating literals
            let mut i = 0;
            loop {
                let mut inst = self.get_inst_mut(node);
                if i >= inst.args.len() {
                    break;
                }
                let arg = &mut inst.args[i];
                if let Value::Literal(lit) = arg {
                    match *lit {
                        Literal::Float(f) => {
                            if let Some(r) = float_map.get(&f) {
                                // found
                                *arg = Value::Inst(*r);
                            } else {
                                // construct instruction at beginning
                                let bits = f.get().to_bits();
                                let hi = bits >> 13;
                                let lo = bits & 0x1FFF;
                                eprintln!("Convert floating point literal {:?}", f.get());
                                let name = format!("T_f_{:?}", f.get()).replace(".", "_");
                                let replaced = if lo == 0 {
                                    // T1 = lu_imm(hi)
                                    drop(inst);
                                    self.insert_head(Inst {
                                        prev: None,
                                        next: None,
                                        lhs: name,
                                        op: "lu_imm".to_string(),
                                        args: vec![Value::Literal(Literal::Integer(hi as i32))],
                                        use_set: vec![],
                                    })
                                } else {
                                    // T1 = lu_imm(hi)
                                    // T2 = or_i_imm(T1, lo)
                                    drop(inst);
                                    let ori = self.insert_head(Inst {
                                        prev: None,
                                        next: None,
                                        lhs: name,
                                        op: "or_i_imm".to_string(),
                                        args: vec![Value::Literal(Literal::Integer(lo as i32))],
                                        use_set: vec![],
                                    });
                                    let lui = self.insert_head(Inst {
                                        prev: None,
                                        next: None,
                                        lhs: format!("T_f_hi_{:?}", f.get()).replace(".", "_"),
                                        op: "lu_imm".to_string(),
                                        args: vec![Value::Literal(Literal::Integer(hi as i32))],
                                        use_set: vec![],
                                    });

                                    // fixup
                                    let mut inst = self.get_inst_mut(ori);
                                    inst.args.insert(0, Value::Inst(lui));
                                    ori
                                };
                                float_map.insert(f, replaced);

                                // replace arg
                                let mut inst = self.get_inst_mut(node);
                                inst.args[i] = Value::Inst(replaced);
                            }
                        }
                        Literal::Integer(num) => {
                            // TODO
                            let bits = num as u32;
                            if inst.op == "move" {
                                // lhs = move(int)
                                let hi = bits >> 13;
                                let lo = bits & 0x1FFF;
                                if lo == 0 {
                                    // lhs = lu_imm(hi)
                                    drop(inst);

                                    let mut inst = self.get_inst_mut(node);
                                    inst.op = "lu_imm".to_string();
                                    inst.args = vec![Value::Literal(Literal::Integer(hi as i32))];
                                } else {
                                    unimplemented!()
                                }
                            } else if !inst.op.ends_with("_imm") {
                                if inst.op == "gt_i" || inst.op == "sub_i" {
                                    inst.op = format!("{}_imm", &inst.op);
                                } else {
                                    unimplemented!("not implemented: {}", inst.op);
                                }
                            }
                        }
                    }
                }
                i += 1;
            }

            node_opt = next;
        }
    }

    pub fn literal_to_mem(&mut self) {
        let mut variables: HashSet<String> = HashSet::new();

        // collect all variables
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let mut inst = self.get_inst_mut(node);
            let next = inst.next;
            for arg in &mut inst.args {
                if let Value::Variable(var) = arg {
                    variables.insert(var.clone());
                }
            }
            if !inst.lhs.starts_with("T_") {
                variables.insert(inst.lhs.clone());
            }

            node_opt = next;
        }

        // lift at most 32-variables.len() literals
        let avail = 32 - variables.len();
        if avail == 0 {
            // no more place
            return;
        }

        // collect all large literals
        // map: Literal -> cost
        let mut large_literals: HashMap<Literal, u32> = HashMap::new();
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let mut inst = self.get_inst_mut(node);
            let next = inst.next;

            for arg in &mut inst.args {
                if let Value::Literal(lit) = arg {
                    if let Literal::Float(f) = lit {
                        let bits = f.get().to_bits();
                        let lo = bits & 0x1FFF;
                        if lo == 0 {
                            // weight = 1
                            large_literals.insert(lit.clone(), 1);
                        } else {
                            // weight = 2
                            large_literals.insert(lit.clone(), 2);
                        }
                    } else if let Literal::Integer(i) = lit {
                        if (*i & !(0x1FFF)) != 0 {
                            // requires lifting
                            large_literals.insert(lit.clone(), 2);
                        }
                    }
                }
            }

            node_opt = next;
        }

        // find at most avail number of literals sorted by cost
        let mut literals: Vec<(Literal, u32)> = large_literals.into_iter().collect();
        literals.sort_by_key(|(_lit, cost)| *cost);
        literals.reverse();
        if literals.len() > avail {
            literals.drain(avail..);
            assert!(literals.len() == avail);
        }
        for (lit, _cost) in &literals {
            eprintln!("Lift {:?} to memory", lit);
        }
        let large_literals: HashMap<Literal, u32> = literals.into_iter().collect();

        // lift large literals
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let mut inst = self.get_inst_mut(node);
            let next = inst.next;

            for arg in &mut inst.args {
                if let Value::Literal(lit) = arg {
                    if large_literals.contains_key(lit) {
                        if let Literal::Float(f) = lit {
                            *arg = Value::Variable(format!("C_f_{:?}", f.get()).replace(".", "_"));
                        } else if let Literal::Integer(f) = lit {
                            *arg = Value::Variable(format!("C_i_{:?}", f).replace(".", "_"));
                        }
                    }
                }
            }

            node_opt = next;
        }
    }

    pub fn optimize(&mut self) {
        for _ in 0..5 {
            self.analyze();
            self.fma();
            self.math();
            self.dce();
            self.peephole();
            self.cse();
            self.literal_to_mem();
        }
    }

    pub fn instructions(&self) -> usize {
        let mut res = 0;
        let mut node_opt = *self.head.borrow();
        while let Some(node) = node_opt {
            let inst = self.get_inst(node);
            res += 1;
            node_opt = inst.next;
        }
        res
    }
}
