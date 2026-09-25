from pikpak_tool.cli import build_parser
from pikpak_tool.commands.rename import plan_renames


def test_plan_renames_only_changes_basename():
    paths = ["광고/a광고.mp4", "b.mp4", "dir/광고"]
    assert plan_renames(paths, "광고") == [("광고/a광고.mp4", "광고/a.mp4")]


def test_parser_rename_args():
    args = build_parser().parse_args(
        ["--remote", "pp:", "rename", "-f", "/A", "-r", "x", "--dry-run"]
    )
    assert (args.command, args.remote, args.folder, args.remove, args.dry_run) == (
        "rename",
        "pp:",
        "/A",
        "x",
        True,
    )
