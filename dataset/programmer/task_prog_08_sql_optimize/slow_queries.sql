-- =====================================================
-- 慢查询报告 - 生产环境超时 SQL（prog_08 输入）
-- 数据库：MySQL 8.0，主表 orders 约 5M 行
-- =====================================================

-- ─────────────────────────────────────────────────────
-- Q1：按月统计订单金额（响应时间 > 8s）
-- 问题：对 created_at 使用 DATE_FORMAT 函数导致索引失效
-- EXPLAIN 摘要：type=ALL, rows=5120000, Extra=Using filesort
-- ─────────────────────────────────────────────────────
SELECT
    DATE_FORMAT(created_at, '%Y-%m') AS month,
    COUNT(*)                          AS order_count,
    SUM(amount)                       AS total_amount
FROM orders
WHERE DATE_FORMAT(created_at, '%Y-%m') >= '2025-01'
GROUP BY DATE_FORMAT(created_at, '%Y-%m')
ORDER BY month;

-- ─────────────────────────────────────────────────────
-- Q2：查询每个用户的最新一笔订单（响应时间 > 12s）
-- 问题：相关子查询对每行执行一次扫描，形成 N+1 问题
-- EXPLAIN 摘要：DEPENDENT SUBQUERY, type=ALL per row
-- ─────────────────────────────────────────────────────
SELECT
    u.id,
    u.username,
    u.email,
    (SELECT o.amount
     FROM orders o
     WHERE o.user_id = u.id
     ORDER BY o.created_at DESC
     LIMIT 1) AS latest_order_amount
FROM users u
WHERE u.status = 'active';

-- ─────────────────────────────────────────────────────
-- Q3：导出活跃用户的全量订单明细（响应时间 > 30s）
-- 问题：无 LIMIT，返回数据量不可控（当前约 180 万行）
-- EXPLAIN 摘要：type=ref, rows=1800000, Extra=Using temporary
-- ─────────────────────────────────────────────────────
SELECT
    u.username,
    u.email,
    o.id          AS order_id,
    o.amount,
    o.status,
    o.created_at
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE u.status = 'active'
  AND o.status IN ('completed', 'refunded')
ORDER BY o.created_at DESC;
