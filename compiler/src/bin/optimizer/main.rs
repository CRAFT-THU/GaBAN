use std::path::PathBuf;
use structopt::StructOpt;

#[derive(Debug, StructOpt)]
#[structopt(name = "compiler")]
struct Opt {
    /// Input file
    #[structopt(parse(from_os_str))]
    input: PathBuf,
}

fn main() -> anyhow::Result<()> {
    let opt = Opt::from_args();
    let mut program = compiler::Program::new();
    program.parse(opt.input)?;
    program.analyze();
    program.optimize();
    program.lower();
    program.analyze();
    program.optimize();
    print!("{}", program.dump());
    Ok(())
}
