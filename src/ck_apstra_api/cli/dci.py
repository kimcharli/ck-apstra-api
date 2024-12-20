import click

from . import cliVar, prep_logging

@click.command()
@click.option('--bp-name', type=str, envvar='BP_NAME', help='Blueprint name')
@click.pass_context
def export_dci(ctx, bp_name: str):
    """
    Export the DCI information

    \b
    The headers:
    """
    logger = prep_logging('DEBUG', 'export_iplink()')

    bp = cliVar.get_blueprint(bp_name, logger)
    if not bp:
        return

    print(f"{cliVar.export_data=}")    
    # print(f"{bp=}")

