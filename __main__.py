"""Enables `python -m mdslides`."""
if __package__:
    from .mdslides import main
else:  # 直接运行 __main__.py 的兜底
    from mdslides import main

if __name__ == "__main__":
    raise SystemExit(main())
