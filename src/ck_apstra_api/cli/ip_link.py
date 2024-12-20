from functools import cache
import click
import csv
import os

from result import Ok, Err

from ck_apstra_api import CkApstraBlueprint, IpLinkEnum, CtCsvKeys, import_ip_link_ct

from . import prep_logging, cliVar

@click.command()
@click.option('--csv-out', type=str, default='iplink-out.csv', help='CSV file name to create')
@click.pass_context
def export_iplink(ctx, csv_out: str = None):
    """
    Export the IP Links into a CSV file

    \b
    The headers:
        line, blueprint, switch, interface, ipv4_switch, ipv4_server, server
    """
    logger = prep_logging('DEBUG', 'export_iplink()')

    if cliVar.session.last_error:
        logger.error(f"Session error: {cliVar.session.last_error}")
        return

    iplinks = []
    lines = 1
    blueprint_ids = cliVar.session.list_blueprint_ids()
    for bp_id in blueprint_ids:
        bp = CkApstraBlueprint(cliVar.session, label=None, id=bp_id)
        if not bp.id:
            logger.error(f"Blueprint {bp_id} not found")
            continue
        bp_label = bp.label
        logger.info(f"{bp_label=}")

        iplinks_in_bp = bp.export_iplink()
        if isinstance(iplinks_in_bp, Err):
            logger.error(iplinks.err_value)
            return
        logger.info(f"{iplinks_in_bp.ok_value=}")
        for iplink in iplinks_in_bp.ok_value:
            iplink[IpLinkEnum.HEADER_LINE] = lines
            lines += 1
            iplinks.append(iplink)
            logger.info(f"{iplink=}")

    csv_path = os.path.expanduser(f"{csv_out}")
    with open(csv_path, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=iplinks[0].keys())
        writer.writeheader()
        writer.writerows(iplinks)
    logger.info(f"IP Links exported to {csv_path}")

@cache
def get_blueprint(session, bp_name):
    from ck_apstra_api import CkApstraBlueprint
    bp = CkApstraBlueprint(session, bp_name)
    return bp


@click.command()
@click.option('--csv-in', type=str, default='iplink-in.csv', help='CSV file name to read IpLinks')
@click.pass_context
def import_iplink(ctx, csv_in: str = None):
    """
    Import the IP Links from a CSV file.

    \b
    Sample CSV file: https://github.com/kimcharli/ck-apstra-api/blob/main/tests/fixtures/iplink_sample.csv
    The CSV file from export_iplink can be used as the sample as well.
    The headers:
        line, blueprint, switch, interface, ipv4_switch, ipv4_server, server
    """
    logger = prep_logging('DEBUG', 'import_iplink()')

    if cliVar.session.last_error:
        logger.error(f"Session error: {cliVar.session.last_error}")
        return

    ip_links_to_add = []
    with open(csv_in, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        headers = next(csv_reader)  # Read the header row
        expected_headers = [header.value for header in IpLinkEnum]
        if sorted(headers) != sorted(expected_headers):
            raise ValueError(f"CSV header {headers} mismatch.\n    Expected headers: {expected_headers}")

        for row in csv_reader:
            dict_to_add = dict(zip(headers, row))
            ip_links_to_add.append(dict_to_add)
            # logger.info(f"{dict_to_add=}")
            blueprint_label = dict_to_add[IpLinkEnum.HEADER_BLUEPRINT]
            bp = get_blueprint(cliVar.session, blueprint_label)
            if not bp.id:
                logger.error(f"Blueprint {blueprint_label} not found")
                continue
            patched = bp.import_iplink(dict_to_add)
            if isinstance(patched, Err):
                logger.error(patched.err_value)
                continue
            logger.info(f"{patched.ok_value}")


@click.command()
@click.option('--csv-in', type=str, default='~/Downloads/iplink_ct.csv', help='Path to the CSV file for iplink CT')
@click.pass_context
def import_iplink_ct(ctx, csv_in: str):
    """
    Import IpLink Connectivity Template from a CSV file

    \b
    Use label 'Default routing zone' for the default routing zone.
    Sample CSV file: https://raw.githubusercontent.com/kimcharli/ck-apstra-api/main/tests/fixtures/iplink_ct_sample.csv
    """
    logger = prep_logging('DEBUG', 'import_iplink_ct()')

    if cliVar.session.last_error:
        logger.error(f"Session error: {cliVar.session.last_error}")
        return
    csv_path = os.path.expanduser(csv_in)

    cts_to_add = []
    with open(csv_path, 'r') as csvfile:
        csv_reader = csv.reader(csvfile)
        headers = next(csv_reader)  # Read the header row
        expected_headers = [header.value for header in CtCsvKeys]
        if sorted(headers) != sorted(expected_headers):
            raise ValueError(f"CSV header {headers} mismatch.\n    Expected headers: {expected_headers}")
        for row in csv_reader:
            in_dict = dict(zip(headers, row))
            in_dict['interface_type'] = 'tagged' if in_dict[CtCsvKeys.TAGGED] == 'yes' else 'untagged'
            del in_dict[CtCsvKeys.TAGGED]
            in_dict['ipv4_addressing_type'] = 'numbered' if in_dict[CtCsvKeys.IPV4] == 'yes' else 'none'
            del in_dict[CtCsvKeys.IPV4]
            in_dict['ipv6_addressing_type'] = 'numbered' if in_dict[CtCsvKeys.IPV6] == 'yes' else 'none'
            del in_dict[CtCsvKeys.IPV6]
            cts_to_add.append(in_dict)

    for res in import_ip_link_ct(cliVar.session, cts_to_add):
        if isinstance(res, Ok):
            logger.info(res.ok_value)
        elif isinstance(res, Err):
            logger.warning(res.err_value)

