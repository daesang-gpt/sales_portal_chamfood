const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

// 스크린샷 저장 디렉토리 생성
const screenshotDir = path.join(__dirname, 'screenshots');
if (!fs.existsSync(screenshotDir)) {
  fs.mkdirSync(screenshotDir);
}

// 캡처할 페이지 목록
const pages = [
  { name: 'dashboard', url: 'http://localhost:3000' },
  { name: 'sales-reports', url: 'http://localhost:3000/sales-reports' },
  { name: 'companies', url: 'http://localhost:3000/companies' },
  { name: 'login', url: 'http://localhost:3000/login' },
  { name: 'register', url: 'http://localhost:3000/register' },
  { name: 'mypage', url: 'http://localhost:3000/mypage' },
  { name: 'admin', url: 'http://localhost:3000/admin' },
  { name: 'analytics', url: 'http://localhost:3000/analytics' },
  { name: 'prospects', url: 'http://localhost:3000/prospects' }
];

async function takeScreenshots() {
  console.log('브라우저를 시작합니다...');
  const browser = await puppeteer.launch({
    headless: false, // 브라우저 창을 보이게 설정
    defaultViewport: { width: 1920, height: 1080 },
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  try {
    for (const page of pages) {
      console.log(`${page.name} 페이지 스크린샷을 찍는 중...`);
      
      const browserPage = await browser.newPage();
      
      // 페이지 로드 대기
      await browserPage.goto(page.url, { 
        waitUntil: 'networkidle2',
        timeout: 30000 
      });

      // 페이지가 완전히 로드될 때까지 잠시 대기
      await new Promise(resolve => setTimeout(resolve, 3000));

      // 스크린샷 찍기
      const screenshotPath = path.join(screenshotDir, `${page.name}.png`);
      await browserPage.screenshot({
        path: screenshotPath,
        fullPage: true
      });

      console.log(`✅ ${page.name} 스크린샷 저장됨: ${screenshotPath}`);
      
      await browserPage.close();
    }
    
    console.log('🎉 모든 스크린샷이 완료되었습니다!');
    console.log(`📁 저장 위치: ${screenshotDir}`);
    
  } catch (error) {
    console.error('스크린샷 찍기 중 오류 발생:', error);
  } finally {
    await browser.close();
  }
}

// 스크립트 실행
takeScreenshots().catch(console.error); 