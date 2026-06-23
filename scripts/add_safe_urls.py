import pandas as pd

safe_urls = [
    'https://www.google.com', 'https://github.com', 'https://stackoverflow.com',
    'https://www.youtube.com', 'https://www.facebook.com', 'https://www.amazon.com',
    'https://www.reddit.com', 'https://www.wikipedia.org', 'https://www.twitter.com',
    'https://www.linkedin.com', 'https://www.instagram.com', 'https://www.netflix.com',
    'https://www.apple.com', 'https://www.microsoft.com', 'https://www.dropbox.com',
    'https://www.whatsapp.com', 'https://www.zoom.us', 'https://www.slack.com',
    'https://www.notion.so', 'https://www.figma.com', 'https://www.atlassian.com',
    'https://vercel.com', 'https://netlify.com', 'https://www.digitalocean.com',
    'https://www.cloudflare.com', 'https://www.mongodb.com', 'https://www.postgresql.org',
    'https://www.docker.com', 'https://www.nginx.com', 'https://www.linux.org',
    'https://www.python.org', 'https://nodejs.org', 'https://react.dev',
    'https://www.npmjs.com', 'https://pypi.org',
    'https://mail.google.com', 'https://drive.google.com', 'https://docs.google.com',
    'https://calendar.google.com', 'https://meet.google.com',
    'https://news.ycombinator.com', 'https://medium.com', 'https://dev.to',
    'https://www.typescriptlang.org', 'https://aws.amazon.com',
    'https://www.cnn.com', 'https://www.bbc.com', 'https://www.nytimes.com',
    'https://www.wsj.com', 'https://www.bloomberg.com', 'https://www.forbes.com',
    'https://www.wired.com', 'https://www.theverge.com', 'https://techcrunch.com',
    'https://www.arstechnica.com', 'https://www.quora.com', 'https://www.ebay.com',
    'https://www.bestbuy.com', 'https://www.walmart.com', 'https://www.target.com',
    'https://www.spotify.com', 'https://www.soundcloud.com', 'https://www.twitch.tv',
    'https://discord.com', 'https://telegram.org', 'https://www.snapchat.com',
    'https://www.tiktok.com', 'https://www.pinterest.com', 'https://www.tumblr.com',
    'https://www.adobe.com', 'https://www.salesforce.com', 'https://www.oracle.com',
    'https://www.ibm.com', 'https://www.intel.com', 'https://www.nvidia.com',
    'https://www.samsung.com', 'https://www.sony.com',
    'https://www.hp.com', 'https://www.dell.com', 'https://www.lenovo.com',
    'https://www.uber.com', 'https://www.lyft.com', 'https://www.airbnb.com',
    'https://www.expedia.com', 'https://www.booking.com', 'https://www.tripadvisor.com',
    'https://www.yelp.com', 'https://www.zillow.com',
    'https://www.paypal.com', 'https://www.stripe.com', 'https://www.squareup.com',
    'https://www.chase.com', 'https://www.bankofamerica.com', 'https://www.wellsfargo.com',
    'https://www.citi.com', 'https://www.capitalone.com', 'https://www.americanexpress.com',
    'https://www.usps.com', 'https://www.fedex.com', 'https://www.ups.com',
    'https://www.dhl.com', 'https://www.cvs.com', 'https://www.walgreens.com',
    'https://www.united.com', 'https://www.delta.com', 'https://www.southwest.com',
    'https://www.marriott.com', 'https://www.hilton.com',
    'https://www.statefarm.com', 'https://www.allstate.com', 'https://www.geico.com',
    'https://www.progressive.com', 'https://www.nationwide.com',
    'https://www.usatoday.com', 'https://www.reuters.com',
    'https://www.npr.org', 'https://www.pbs.org', 'https://www.bbc.co.uk',
    'https://www.aljazeera.com', 'https://www.economist.com',
    'https://www.nationalgeographic.com', 'https://www.nature.com',
    'https://www.science.org', 'https://www.ieee.org', 'https://www.acm.org',
    'https://www.coursera.org', 'https://www.edx.org', 'https://www.udemy.com',
    'https://www.khanacademy.org', 'https://www.codecademy.com',
    'https://developers.google.com', 'https://docs.github.com',
    'https://support.microsoft.com', 'https://learn.microsoft.com',
    'https://www.redhat.com', 'https://www.ubuntu.com', 'https://www.debian.org',
    'https://git-scm.com', 'https://curl.se', 'https://www.openssl.org',
    'https://www.apache.org', 'https://www.eclipse.org',
    'https://www.jetbrains.com', 'https://code.visualstudio.com',
    'https://getbootstrap.com', 'https://tailwindcss.com',
    'https://angular.io', 'https://vuejs.org', 'https://svelte.dev',
    'https://nextjs.org', 'https://nuxt.com', 'https://astro.build',
    'https://wordpress.org', 'https://www.drupal.org', 'https://laravel.com',
    'https://www.djangoproject.com', 'https://flask.palletsprojects.com',
    'https://expressjs.com', 'https://fastapi.tiangolo.com',
    'https://spring.io', 'https://www.postman.com',
    'https://graphql.org', 'https://www.mysql.com', 'https://www.sqlite.org',
    'https://redis.io', 'https://www.elastic.co', 'https://www.rabbitmq.com',
    'https://kubernetes.io', 'https://www.terraform.io',
    'https://www.jenkins.io', 'https://about.gitlab.com', 'https://bitbucket.org',
    'https://www.openai.com', 'https://huggingface.co', 'https://pytorch.org',
    'https://www.tensorflow.org', 'https://scikit-learn.org',
    'https://pandas.pydata.org', 'https://numpy.org', 'https://matplotlib.org',
    'https://jupyter.org', 'https://www.kaggle.com', 'https://www.datacamp.com',
    'https://www.splunk.com', 'https://www.datadoghq.com',
    'https://www.grafana.com', 'https://prometheus.io',
    'https://trello.com', 'https://asana.com', 'https://monday.com',
    'https://clickup.com', 'https://mailchimp.com', 'https://www.hubspot.com',
    'https://www.twilio.com', 'https://www.zendesk.com', 'https://www.intercom.com',
    'https://www.shopify.com', 'https://www.wix.com', 'https://www.squarespace.com',
    'https://www.webflow.com', 'https://www.hashicorp.com',
    'https://www.cncf.io', 'https://www.linuxfoundation.org',
    'https://www.mozilla.org', 'https://www.eff.org',
    'https://www.opensource.org', 'https://www.gnu.org', 'https://www.kernel.org',
    'https://www.phoronix.com', 'https://www.cnet.com',
    'https://www.zdnet.com', 'https://www.techradar.com',
    'https://www.anandtech.com', 'https://www.gsmarena.com',
    'https://www.xda-developers.com', 'https://www.macrumors.com',
    'https://www.windowscentral.com', 'https://www.androidcentral.com',
    'https://github.com/torvalds/linux', 'https://github.com/python/cpython',
    'https://github.com/nodejs/node', 'https://github.com/facebook/react',
    'https://github.com/vuejs/vue', 'https://github.com/twbs/bootstrap',
    'https://github.com/tailwindlabs/tailwindcss',
    'https://github.com/microsoft/vscode', 'https://github.com/numpy/numpy',
    'https://github.com/pandas-dev/pandas', 'https://github.com/scikit-learn/scikit-learn',
    'https://github.com/pytorch/pytorch', 'https://github.com/tensorflow/tensorflow',
    'https://github.com/huggingface/transformers',
    'https://github.com/kubernetes/kubernetes', 'https://github.com/docker/compose',
    'https://github.com/hashicorp/terraform', 'https://github.com/ansible/ansible',
    'https://github.com/prometheus/prometheus', 'https://github.com/grafana/grafana',
    'https://github.com/elastic/elasticsearch', 'https://github.com/redis/redis',
    'https://github.com/mongodb/mongo', 'https://github.com/postgres/postgres',
    'https://github.com/mysql/mysql-server',
    'https://github.com/nginx/nginx', 'https://github.com/llvm/llvm-project',
    'https://github.com/gcc-mirror/gcc', 'https://github.com/rust-lang/rust',
    'https://github.com/golang/go', 'https://github.com/microsoft/TypeScript',
    'https://github.com/vim/vim', 'https://github.com/git/git',
    'https://github.com/curl/curl', 'https://github.com/openssl/openssl',
    'https://github.com/apache/kafka', 'https://github.com/facebook/jest',
    'https://github.com/pallets/flask', 'https://github.com/expressjs/express',
    'https://github.com/laravel/laravel', 'https://github.com/vitejs/vite',
    'https://github.com/Homebrew/brew', 'https://github.com/npm/cli',
    'https://github.com/babel/babel', 'https://github.com/webpack/webpack',
    'https://github.com/rollup/rollup', 'https://github.com/eslint/eslint',
    'https://github.com/prettier/prettier',
]

df = pd.read_csv('data/phishing_site_urls.csv')
df = df.drop_duplicates()

extra_urls = list(safe_urls)
import random
random.seed(42)

common_prefixes = ['', 'www.', 'mail.', 'blog.', 'shop.', 'help.', 'support.', 'docs.', 'api.', 'dev.', 'app.', 'admin.', 'portal.', 'status.', 'community.', 'forum.', 'news.', 'info.', 'careers.', 'jobs.', 'partners.', 'investors.', 'developers.', 'cloud.', 'my.', 'login.', 'account.', 'service.', 'store.', 'media.', 'cdn.']
common_suffixes = ['', '/', '/index.html', '/home', '/about', '/contact', '/blog', '/login', '/signup', '/pricing', '/features', '/docs', '/api', '/help', '/support', '/terms', '/privacy', '/status']
common_subpages = ['/products', '/services', '/solutions', '/resources', '/download', '/apps', '/integrations', '/changelog', '/roadmap', '/tutorials', '/guides', '/faq']

additional = []
for domain in ['google', 'facebook', 'amazon', 'microsoft', 'apple', 'netflix', 'twitter', 'instagram', 'linkedin', 'github', 'reddit', 'youtube', 'whatsapp', 'telegram', 'snapchat', 'tiktok', 'spotify', 'zoom', 'slack', 'dropbox', 'adobe', 'salesforce', 'oracle', 'ibm', 'intel', 'nvidia', 'samsung', 'huawei', 'cisco', 'vmware', 'sap', 'dell', 'hp', 'lenovo', 'accenture', 'uber', 'airbnb', 'paypal', 'stripe', 'shopify', 'godaddy', 'namecheap', 'cloudflare', 'digitalocean', 'heroku', 'vercel', 'netlify', 'python', 'node', 'golang', 'rustlang', 'typescript', 'mongodb', 'postgres', 'mysql', 'sqlite', 'docker', 'kubernetes', 'jenkins', 'gitlab', 'bitbucket']:
    for tld in ['.com', '.org', '.net', '.io', '.co', '.app', '.dev', '.ai']:
        for prefix in random.sample(common_prefixes, 3):
            d = prefix + domain + tld + random.choice(common_suffixes)
            if d.startswith('.'):
                d = d[1:]
            if not d.startswith('http'):
                d = 'https://' + d
            additional.append(d)

extra_urls.extend(additional)

extra_urls_2 = []
real_domains = ['google.com', 'facebook.com', 'amazon.com', 'microsoft.com', 'apple.com',
                'netflix.com', 'twitter.com', 'instagram.com', 'linkedin.com', 'github.com',
                'reddit.com', 'youtube.com', 'spotify.com', 'zoom.us', 'slack.com',
                'dropbox.com', 'adobe.com', 'salesforce.com', 'oracle.com', 'ibm.com',
                'intel.com', 'nvidia.com', 'samsung.com', 'cisco.com', 'vmware.com',
                'dell.com', 'hp.com', 'lenovo.com', 'uber.com', 'airbnb.com',
                'paypal.com', 'stripe.com', 'shopify.com', 'cloudflare.com',
                'digitalocean.com', 'vercel.com', 'netlify.com', 'docker.com',
                'kubernetes.io', 'gitlab.com', 'bitbucket.org', 'atlassian.com',
                'mongodb.com', 'postgresql.org', 'mysql.com', 'redis.io',
                'elastic.co', 'nginx.com', 'apache.org', 'python.org',
                'nodejs.org', 'golang.org', 'rust-lang.org', 'typescriptlang.org',
                'react.dev', 'nextjs.org', 'nuxt.com', 'astro.build',
                'wordpress.org', 'laravel.com', 'djangoproject.com', 'rails.org',
                'spring.io', 'expressjs.com', 'fastapi.tiangolo.com']

path_variations = ['/', '/home', '/about', '/contact', '/blog', '/news', '/products',
                   '/solutions', '/pricing', '/docs', '/api', '/help', '/support',
                   '/careers', '/login', '/signup', '/features', '/integrations',
                   '/changelog', '/roadmap', '/faq', '/terms', '/privacy',
                   '/download', '/apps', '/resources', '/tutorials', '/guides',
                   '/services', '/portfolio', '/gallery', '/events', '/partners']

for domain in real_domains:
    for path in random.sample(path_variations, 5):
        extra_urls_2.append(f'https://www.{domain}{path}')
        extra_urls_2.append(f'https://{domain}{path}')

extra_urls.extend(extra_urls_2)

new_good = pd.DataFrame({'URL': extra_urls, 'Label': ['good'] * len(extra_urls)})
df = pd.concat([df, new_good], ignore_index=True)
df = df.drop_duplicates(subset='URL')

print(f'Total: {len(df)}')
print(f'Good: {len(df[df["Label"]=="good"])}, Bad: {len(df[df["Label"]=="bad"])}')
df.to_csv('data/phishing_site_urls.csv', index=False)
print('Done!')
