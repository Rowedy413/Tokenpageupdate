#!/usr/bin/env python3

import os
import sys
import re
import json
from flask import Flask, render_template_string, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup as BS

app = Flask(__name__)

DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36"
THREADS = 12

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto Page Creator - ROWEDY</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .header h1 {
            color: white;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            margin-bottom: 10px;
        }

        .header p {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1em;
        }

        .main-card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        }

        .form-group {
            margin-bottom: 25px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 1.1em;
        }

        .form-group textarea,
        .form-group input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1em;
            transition: border-color 0.3s;
            font-family: 'Courier New', monospace;
        }

        .form-group textarea:focus,
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }

        .form-group textarea {
            resize: vertical;
            min-height: 120px;
        }

        .form-group small {
            display: block;
            margin-top: 5px;
            color: #666;
            font-size: 0.9em;
        }

        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            border-radius: 10px;
            font-size: 1.1em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .results {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            max-height: 500px;
            overflow-y: auto;
        }

        .result-item {
            background: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }

        .result-item.success {
            border-left-color: #28a745;
        }

        .result-item.error {
            border-left-color: #dc3545;
        }

        .result-item h4 {
            margin-bottom: 8px;
            color: #333;
        }

        .result-item p {
            color: #666;
            font-size: 0.95em;
            margin: 5px 0;
        }

        .result-item a {
            color: #667eea;
            text-decoration: none;
            word-break: break-all;
        }

        .result-item a:hover {
            text-decoration: underline;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }

        .loading.active {
            display: block;
        }

        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .stats {
            display: flex;
            justify-content: space-around;
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }

        .stat-item {
            text-align: center;
        }

        .stat-item h3 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 5px;
        }

        .stat-item p {
            color: #666;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ROWEDY Auto Page Creator</h1>
            <p>Create Facebook pages automatically with custom names and profile pictures</p>
        </div>

        <div class="main-card">
            <form id="pageForm">
                <div class="form-group">
                    <label for="cookies">Facebook Cookies (One per line)</label>
                    <textarea id="cookies" name="cookies" required placeholder="Paste your Facebook cookies here (one per line)"></textarea>
                    <small>Each line should contain a complete Facebook cookie string</small>
                </div>

                <div class="form-group">
                    <label for="pageNames">Page Names (One per line)</label>
                    <textarea id="pageNames" name="pageNames" required placeholder="Enter page names (one per line, must match number of cookies)"></textarea>
                    <small>Enter the same number of page names as cookies</small>
                </div>

                <div class="form-group">
                    <label for="imageUrl">Profile Picture URL (Optional)</label>
                    <input type="text" id="imageUrl" name="imageUrl" placeholder="https://example.com/image.jpg">
                    <small>Enter a direct URL to the image you want as profile picture</small>
                </div>

                <div class="form-group">
                    <label for="userAgent">User Agent (Optional)</label>
                    <input type="text" id="userAgent" name="userAgent" placeholder="Leave empty for default">
                    <small>Custom user agent string (optional)</small>
                </div>

                <button type="submit" class="btn" id="submitBtn">Create Pages</button>
            </form>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 15px; color: #666;">Creating pages, please wait...</p>
            </div>

            <div class="stats" id="stats" style="display: none;">
                <div class="stat-item">
                    <h3 id="totalCount">0</h3>
                    <p>Total Processed</p>
                </div>
                <div class="stat-item">
                    <h3 id="successCount" style="color: #28a745;">0</h3>
                    <p>Success</p>
                </div>
                <div class="stat-item">
                    <h3 id="errorCount" style="color: #dc3545;">0</h3>
                    <p>Failed</p>
                </div>
            </div>

            <div class="results" id="results" style="display: none;"></div>
        </div>
    </div>

    <script>
        const form = document.getElementById('pageForm');
        const loading = document.getElementById('loading');
        const results = document.getElementById('results');
        const stats = document.getElementById('stats');
        const submitBtn = document.getElementById('submitBtn');

        let totalCount = 0;
        let successCount = 0;
        let errorCount = 0;

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const cookies = document.getElementById('cookies').value.trim().split('\n').filter(c => c.trim());
            const pageNames = document.getElementById('pageNames').value.trim().split('\n').filter(n => n.trim());
            const imageUrl = document.getElementById('imageUrl').value.trim();
            const userAgent = document.getElementById('userAgent').value.trim();

            if (cookies.length !== pageNames.length) {
                alert('Number of cookies and page names must match!');
                return;
            }

            submitBtn.disabled = true;
            loading.classList.add('active');
            results.innerHTML = '';
            results.style.display = 'none';
            stats.style.display = 'none';
            totalCount = 0;
            successCount = 0;
            errorCount = 0;

            try {
                const response = await fetch('/create_pages', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        cookies: cookies,
                        page_names: pageNames,
                        image_url: imageUrl,
                        user_agent: userAgent
                    })
                });

                const data = await response.json();
                
                loading.classList.remove('active');
                results.style.display = 'block';
                stats.style.display = 'flex';

                data.results.forEach(result => {
                    totalCount++;
                    const div = document.createElement('div');
                    div.className = 'result-item ' + (result.success ? 'success' : 'error');
                    
                    if (result.success) {
                        successCount++;
                        div.innerHTML = `
                            <h4>✓ ${result.page_name}</h4>
                            <p><strong>Profile ID:</strong> ${result.profile_id || 'N/A'}</p>
                            <p><strong>Page ID:</strong> ${result.page_id || 'N/A'}</p>
                            <p><strong>URL:</strong> <a href="${result.url}" target="_blank">${result.url}</a></p>
                        `;
                    } else {
                        errorCount++;
                        div.innerHTML = `
                            <h4>✗ ${result.page_name}</h4>
                            <p><strong>Error:</strong> ${result.error}</p>
                        `;
                    }
                    
                    results.appendChild(div);
                });

                document.getElementById('totalCount').textContent = totalCount;
                document.getElementById('successCount').textContent = successCount;
                document.getElementById('errorCount').textContent = errorCount;

            } catch (error) {
                loading.classList.remove('active');
                alert('An error occurred: ' + error.message);
            } finally {
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
'''

def make_headers(user_agent, cookie_string):
    headers = {
        'authority': 'www.facebook.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': user_agent,
        'cookie': cookie_string
    }
    return headers

def create_single_page(cookie_str, page_name, user_agent):
    headers = make_headers(user_agent, cookie_str)
    session = requests.Session()
    session.headers.update({'user-agent': user_agent})
    
    result = {
        'page_name': page_name,
        'success': False,
        'error': None,
        'profile_id': None,
        'page_id': None,
        'url': None
    }
    
    try:
        r = session.get('https://www.facebook.com/pages/creation/?ref_type=launch_point', 
                       headers=headers, timeout=20)
        
        if r.status_code != 200:
            result['error'] = f'HTTP {r.status_code} Error'
            return result

        html = r.text

        try:
            usr = re.search(r'__user=(.*?)&', html).group(1)
        except:
            m = re.search(r'c_user=(\d+)', cookie_str)
            usr = m.group(1) if m else "0"
        
        try:
            rev = re.search(r'{"rev":(.*?)}', html).group(1)
        except:
            rev = "0"
        
        try:
            dts = re.search(r'"DTSGInitialData",\[\],{"token":"(.*?)"', html).group(1)
        except:
            m = re.search(r'fb_dtsg\"\s*:\s*\"([^"]+)\"', html)
            dts = m.group(1) if m else ""
        
        try:
            jzt = re.search(r'&jazoest=(.*?)",', html).group(1)
        except:
            jzt = ""
        
        try:
            lsd = re.search(r'"LSD",\[\],{"token":"(.*?)"', html).group(1)
        except:
            lsd = ""
        
        try:
            spr = re.search(r'"__spin_r":(.*?),', html).group(1)
        except:
            spr = "0"
        
        try:
            spt = re.search(r'"__spin_t":(.*?),', html).group(1)
        except:
            spt = "0"

        bio_p = "PAGE CREATED BY ROWEDY"

        variables_json = json.dumps({
            "input": {
                "bio": bio_p,
                "categories": ["1350536325044173","200597389954350","123377808095874"],
                "creation_source": "comet",
                "name": page_name,
                "page_referrer": "launch_point",
                "actor_id": usr,
                "client_mutation_id": "3"
            }
        }, separators=(",", ":"))

        data = {
            'av': usr,
            '__user': usr,
            '__a': '1',
            '__req': '1i',
            '__hs': '19666.HYP:comet_pkg.2.1..2.1',
            'dpr': '1',
            '__ccg': 'MODERATE',
            '__rev': rev,
            '__s': 'qvdp97:zb23lw:givv21',
            '__comet_req': '15',
            'fb_dtsg': dts,
            'jazoest': jzt,
            'lsd': lsd,
            '__aaid': '0',
            '__spin_r': spr,
            '__spin_b': 'trunk',
            '__spin_t': spt,
            'fb_api_caller_class': 'RelayModern',
            'fb_api_req_friendly_name': 'AdditionalProfilePlusCreationMutation',
            'variables': variables_json,
            'server_timestamps': 'true',
            'doc_id': '5296879960418435',
        }

        post_headers = headers.copy()
        post_headers.update({
            'content-type': 'application/x-www-form-urlencoded',
            'accept': 'application/json, text/javascript, */*; q=0.01'
        })

        resp = session.post('https://www.facebook.com/api/graphql/', 
                          headers=post_headers, data=data, timeout=25)

        try:
            parsed = resp.json()
            add = parsed.get('data', {}).get('additional_profile_plus_create', {})
            additional_profile_id = add.get('additional_profile', {}).get('id')
            page_id = add.get('page', {}).get('id')
            
            if additional_profile_id or page_id:
                result['success'] = True
                result['profile_id'] = additional_profile_id
                result['page_id'] = page_id
                if page_id:
                    result['url'] = f"https://facebook.com/{page_id}"
                else:
                    result['url'] = f"https://facebook.com/profile.php?id={additional_profile_id}"
            else:
                error_msg = parsed.get('errors') or parsed.get('error_summary')
                result['error'] = str(error_msg)[:100] if error_msg else 'Unknown error'
        except Exception as e:
            result['error'] = f'JSON parse error: {str(e)[:50]}'

    except requests.exceptions.RequestException as e:
        result['error'] = f'Network error: {str(e)[:50]}'
    except Exception as e:
        result['error'] = f'Error: {str(e)[:50]}'
    
    return result

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/create_pages', methods=['POST'])
def create_pages():
    data = request.json
    cookies = data.get('cookies', [])
    page_names = data.get('page_names', [])
    image_url = data.get('image_url', '')
    user_agent = data.get('user_agent', DEFAULT_UA) or DEFAULT_UA
    
    if len(cookies) != len(page_names):
        return jsonify({'error': 'Cookies and page names count mismatch'}), 400
    
    results = []
    
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = []
        for cookie, name in zip(cookies, page_names):
            futures.append(executor.submit(create_single_page, cookie.strip(), name.strip(), user_agent))
        
        for future in futures:
            results.append(future.result())
    
    return jsonify({'results': results})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
