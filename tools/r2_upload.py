"""Copy Chalk & Us episode videos to Cloudflare R2 under chalk-and-us/<file> (same layout as blobby/) and record their
public URLs in queue/r2.json. queue/schedule.csv refers to them as r2:chalk-and-us/<file>; the dashboard looks the URL up in r2.json.

env: R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET, R2_PUBLIC_URL; SRC_DIR (folder with the files); R2_JSON (default queue/r2.json)."""
import glob, json, os, sys, traceback
import boto3, requests


def _hook(t, v, tb):
    msg = (str(v) if t is SystemExit else ''.join(traceback.format_exception_only(t, v))).replace('\n', ' ')
    print('::error title=R2 upload failed::' + msg[:900]); sys.exit(1)



def main():
    for k in ('R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET', 'R2_PUBLIC_URL'):
        if os.environ.get(k):
            os.environ[k] = os.environ[k].strip()   # a pasted secret often has a trailing space or newline
    need = ['R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET', 'R2_PUBLIC_URL']
    missing = [k for k in need if not os.environ.get(k)]
    if missing:
        raise RuntimeError('Missing R2 secrets: ' + ', '.join(missing))
    src = os.environ.get('SRC_DIR', 'videos')
    if not os.path.isdir(src):
        raise RuntimeError(f'no folder {src}')
    s3 = boto3.client('s3', endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
                      aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'], aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'], region_name='auto')
    B, base = os.environ['R2_BUCKET'], os.environ['R2_PUBLIC_URL'].rstrip('/')
    types = {'.mp4': 'video/mp4', '.jpg': 'image/jpeg', '.png': 'image/png', '.srt': 'application/x-subrip'}
    path = os.environ.get('R2_JSON', 'queue/r2.json')
    done = json.load(open(path)) if os.path.exists(path) else {}
    bad = 0
    for f in sorted(glob.glob(f'{src}/*')):
        name = os.path.basename(f)
        key = f'chalk-and-us/{name}'
        size = os.path.getsize(f)
        s3.upload_file(f, B, key, ExtraArgs={'ContentType': types.get(os.path.splitext(name)[1].lower(), 'application/octet-stream')})
        url = f'{base}/{key}'
        h = requests.head(url, timeout=30, allow_redirects=True)
        ok = h.status_code == 200 and int(h.headers.get('content-length', size)) == size
        print(('uploaded ' if ok else 'PROBLEM  ') + key, size, h.status_code)
        if not ok:
            bad += 1
        done[f'r2:{key}'] = {'key': key, 'url': url, 'bytes': size}
    json.dump(done, open(path, 'w'), indent=1)
    if bad:
        raise RuntimeError(f'{bad} file(s) not reachable at the public URL; check R2_PUBLIC_URL / public access')


try:
    main()
except BaseException as e:
    print('::error title=R2 upload failed::' + (''.join(traceback.format_exception_only(type(e), e))).replace('\n', ' ')[:900]); sys.exit(1)
