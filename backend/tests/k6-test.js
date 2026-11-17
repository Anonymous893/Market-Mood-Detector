import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 20,           // 20 virtual users
  duration: '30s',   // run for 30 seconds
  thresholds: {
    http_req_duration: ['p(99)<500'], // p99 < 500ms (adjust based on results)
    http_req_failed: ['rate<0.01'],   // error rate < 1%
  },
};

export default function () {
  const res = http.get('http://localhost:8000/analyse/NVDA'); // change to your endpoint
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(1);
}