from pathlib import Path

import click
import boto3

@click.option('--profile', default = None, help = "Use a given AWS profile")
@click.argument('pathname', type = click.Path(exists = True))
@click.argument('bucketname')
@click.command()
def upload_file(profile, pathname, bucketname):
    """Upload <PATHNAME> to <BUCKETNAME>"""

    session_cfg = {}
    if profile:
        session_cfg['profile_name'] = profile

    AWSSession = boto3.Session(**session_cfg)
    S3 = AWSSession.resource('s3')

    Bucket = S3.Bucket(bucketname)
    FilePath = Path(pathname).expanduser().resolve()

    Bucket.upload_file(str(FilePath), str(FilePath.name))

if __name__ == '__main__':
    upload_file()