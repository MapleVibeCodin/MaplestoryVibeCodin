"""Real Chromium DOM smoke test for delegated selection and injected controls."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=await browser.new_page()
        await page.route('https://henefm.com/**',lambda route:route.fulfill(
            status=200,content_type='text/html',body=(ROOT/'assets/smoke_deals_test.html').read_text()))
        await page.goto('https://henefm.com/flips/deals')
        await page.evaluate("window.__messages=[];window.chrome.runtime={sendMessage:(m,cb)=>{window.__messages.push(m);cb({ok:true});}}")
        await page.evaluate((ROOT/'browser_extension/content.js').read_text())
        await page.wait_for_timeout(250)
        assert await page.locator('[data-fm-rush-controls]').count()==4
        assert not await page.evaluate("__messages.some(m=>m.kind==='fm-rush-select-deal')")
        await page.locator('article').nth(0).locator('a').first.click()
        assert page.url=='https://henefm.com/flips/deals'
        assert await page.evaluate("__messages.at(-1).kind")=='fm-rush-select-deal'
        assert await page.evaluate("__messages.at(-1).deal.ign")=='Hyperborean'
        await page.locator('article').nth(1).get_by_role('button',name='SKIP',exact=True).click()
        assert await page.locator('article').nth(0).get_attribute('data-fm-rush-selected')=='true'
        await page.locator('article').nth(1).get_by_role('button',name='CHASE',exact=True).click()
        assert await page.locator('article').nth(0).get_attribute('data-fm-rush-selected') is None
        assert await page.locator('article').nth(1).get_attribute('data-fm-rush-selected')=='true'
        await page.wait_for_timeout(1300)
        assert await page.locator('[data-fm-rush-controls]').count()==4
        snapshots=await page.evaluate("__messages.filter(m=>m.kind==='fm-rush-visible-deals')")
        assert all('CHASE' not in d['raw_text'] and 'SKIP' not in d['raw_text'] for s in snapshots for d in s['snapshot']['deals'])
        await browser.close()
        print('PASS: Chromium listing click, Chase/Skip, single selection, no duplicate controls, clean parsed metadata')
if __name__=='__main__':asyncio.run(main())
