-- Comprehensive Neon Database Setup Script
-- This script creates sample tables, views, indexes, functions, procedures, triggers, and more
-- for testing the AI Database Tool

-- ============================================
-- 1. CREATE TABLES
-- ============================================

-- Employees table
CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    hire_date DATE NOT NULL,
    job_title VARCHAR(100),
    department_id INTEGER,
    salary DECIMAL(10, 2),
    manager_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Departments table
CREATE TABLE IF NOT EXISTS departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(100),
    budget DECIMAL(12, 2),
    manager_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table
CREATE TABLE IF NOT EXISTS projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(100) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    budget DECIMAL(12, 2),
    status VARCHAR(20) DEFAULT 'active',
    department_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project assignments (many-to-many)
CREATE TABLE IF NOT EXISTS project_assignments (
    assignment_id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    role VARCHAR(50),
    hours_allocated DECIMAL(5, 2),
    start_date DATE,
    end_date DATE,
    UNIQUE(employee_id, project_id)
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending',
    shipping_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items
CREATE TABLE IF NOT EXISTS order_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    product_id INTEGER,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2),
    subtotal DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2),
    stock_quantity INTEGER DEFAULT 0,
    description TEXT,
    supplier_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id SERIAL PRIMARY KEY,
    company_name VARCHAR(100),
    contact_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(50),
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit log table (for triggers)
CREATE TABLE IF NOT EXISTS audit_log (
    log_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100),
    operation VARCHAR(20),
    record_id INTEGER,
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. ADD FOREIGN KEYS
-- ============================================

ALTER TABLE employees 
    ADD CONSTRAINT fk_employees_department 
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE SET NULL;

ALTER TABLE employees 
    ADD CONSTRAINT fk_employees_manager 
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id) ON DELETE SET NULL;

ALTER TABLE departments 
    ADD CONSTRAINT fk_departments_manager 
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id) ON DELETE SET NULL;

ALTER TABLE projects 
    ADD CONSTRAINT fk_projects_department 
    FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE;

ALTER TABLE project_assignments 
    ADD CONSTRAINT fk_assignments_employee 
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE;

ALTER TABLE project_assignments 
    ADD CONSTRAINT fk_assignments_project 
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE CASCADE;

ALTER TABLE orders 
    ADD CONSTRAINT fk_orders_customer 
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL;

ALTER TABLE order_items 
    ADD CONSTRAINT fk_items_order 
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE;

ALTER TABLE order_items 
    ADD CONSTRAINT fk_items_product 
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL;

-- ============================================
-- 3. CREATE INDEXES
-- ============================================

-- B-tree indexes (default)
CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);
CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_employees_manager ON employees(manager_id);
CREATE INDEX IF NOT EXISTS idx_employees_hire_date ON employees(hire_date);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_projects_department ON projects(department_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_employees_name ON employees(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_orders_customer_date ON orders(customer_id, order_date);
CREATE INDEX IF NOT EXISTS idx_project_assignments_emp_proj ON project_assignments(employee_id, project_id);

-- Partial index (only active projects)
CREATE INDEX IF NOT EXISTS idx_projects_active ON projects(project_id) WHERE status = 'active';

-- Expression index (case-insensitive email search)
CREATE INDEX IF NOT EXISTS idx_employees_email_lower ON employees(LOWER(email));

-- ============================================
-- 4. CREATE SEQUENCES (if needed separately)
-- ============================================

-- Sequences are auto-created with SERIAL, but here's an explicit one
CREATE SEQUENCE IF NOT EXISTS seq_custom_id START WITH 1000 INCREMENT BY 1;

-- ============================================
-- 5. CREATE VIEWS
-- ============================================

-- Employee details view
CREATE OR REPLACE VIEW v_employee_details AS
SELECT 
    e.employee_id,
    e.first_name || ' ' || e.last_name AS full_name,
    e.email,
    e.phone,
    e.hire_date,
    e.job_title,
    e.salary,
    d.department_name,
    m.first_name || ' ' || m.last_name AS manager_name
FROM employees e
LEFT JOIN departments d ON e.department_id = d.department_id
LEFT JOIN employees m ON e.manager_id = m.employee_id;

-- Department summary view
CREATE OR REPLACE VIEW v_department_summary AS
SELECT 
    d.department_id,
    d.department_name,
    d.location,
    d.budget,
    COUNT(e.employee_id) AS employee_count,
    AVG(e.salary) AS avg_salary,
    SUM(e.salary) AS total_payroll
FROM departments d
LEFT JOIN employees e ON d.department_id = e.department_id
GROUP BY d.department_id, d.department_name, d.location, d.budget;

-- Project status view
CREATE OR REPLACE VIEW v_project_status AS
SELECT 
    p.project_id,
    p.project_name,
    p.status,
    d.department_name,
    COUNT(pa.employee_id) AS assigned_employees,
    SUM(pa.hours_allocated) AS total_hours
FROM projects p
LEFT JOIN departments d ON p.department_id = d.department_id
LEFT JOIN project_assignments pa ON p.project_id = pa.project_id
GROUP BY p.project_id, p.project_name, p.status, d.department_name;

-- Order summary view
CREATE OR REPLACE VIEW v_order_summary AS
SELECT 
    o.order_id,
    o.order_date,
    c.company_name AS customer_name,
    o.total_amount,
    o.status,
    COUNT(oi.item_id) AS item_count
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON o.order_id = oi.order_id
GROUP BY o.order_id, o.order_date, c.company_name, o.total_amount, o.status;

-- Materialized view (for performance)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_employee_stats AS
SELECT 
    department_id,
    COUNT(*) AS total_employees,
    AVG(salary) AS avg_salary,
    MIN(hire_date) AS earliest_hire,
    MAX(hire_date) AS latest_hire
FROM employees
GROUP BY department_id;

CREATE UNIQUE INDEX ON mv_employee_stats(department_id);

-- ============================================
-- 6. CREATE FUNCTIONS
-- ============================================

-- Function to calculate employee age
CREATE OR REPLACE FUNCTION calculate_employee_age(emp_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    hire_date_val DATE;
    age_years INTEGER;
BEGIN
    SELECT hire_date INTO hire_date_val FROM employees WHERE employee_id = emp_id;
    IF hire_date_val IS NULL THEN
        RETURN NULL;
    END IF;
    age_years := EXTRACT(YEAR FROM AGE(CURRENT_DATE, hire_date_val));
    RETURN age_years;
END;
$$ LANGUAGE plpgsql;

-- Function to get department employees
CREATE OR REPLACE FUNCTION get_department_employees(dept_id INTEGER)
RETURNS TABLE (
    employee_id INTEGER,
    full_name TEXT,
    job_title VARCHAR,
    salary DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.employee_id,
        e.first_name || ' ' || e.last_name AS full_name,
        e.job_title,
        e.salary
    FROM employees e
    WHERE e.department_id = dept_id
    ORDER BY e.last_name, e.first_name;
END;
$$ LANGUAGE plpgsql;

-- Function to update employee salary
CREATE OR REPLACE FUNCTION update_employee_salary(
    emp_id INTEGER,
    new_salary DECIMAL,
    OUT old_salary DECIMAL,
    OUT new_salary_val DECIMAL
) AS $$
BEGIN
    SELECT salary INTO old_salary FROM employees WHERE employee_id = emp_id;
    UPDATE employees SET salary = new_salary WHERE employee_id = emp_id;
    new_salary_val := new_salary;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate order total
CREATE OR REPLACE FUNCTION calculate_order_total(ord_id INTEGER)
RETURNS DECIMAL AS $$
DECLARE
    total DECIMAL;
BEGIN
    SELECT COALESCE(SUM(subtotal), 0) INTO total
    FROM order_items
    WHERE order_id = ord_id;
    
    UPDATE orders SET total_amount = total WHERE order_id = ord_id;
    RETURN total;
END;
$$ LANGUAGE plpgsql;

-- Function with exception handling
CREATE OR REPLACE FUNCTION safe_divide(numerator DECIMAL, denominator DECIMAL)
RETURNS DECIMAL AS $$
BEGIN
    IF denominator = 0 THEN
        RAISE EXCEPTION 'Division by zero is not allowed';
    END IF;
    RETURN numerator / denominator;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 7. CREATE PROCEDURES (PostgreSQL 11+)
-- ============================================

-- Procedure to transfer employee between departments
CREATE OR REPLACE PROCEDURE transfer_employee(
    emp_id INTEGER,
    new_dept_id INTEGER
) AS $$
BEGIN
    UPDATE employees 
    SET department_id = new_dept_id,
        updated_at = CURRENT_TIMESTAMP
    WHERE employee_id = emp_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Employee % not found', emp_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Procedure to archive old orders
CREATE OR REPLACE PROCEDURE archive_old_orders(
    cutoff_date DATE,
    OUT archived_count INTEGER
) AS $$
BEGIN
    WITH archived AS (
        DELETE FROM orders
        WHERE order_date < cutoff_date
        RETURNING order_id
    )
    SELECT COUNT(*) INTO archived_count FROM archived;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 8. CREATE TRIGGERS
-- ============================================

-- Function for update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
CREATE TRIGGER trigger_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function for audit logging
CREATE OR REPLACE FUNCTION audit_table_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, record_id, new_data, changed_by)
        VALUES (TG_TABLE_NAME, 'INSERT', NEW.employee_id, row_to_json(NEW), current_user);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, operation, record_id, old_data, new_data, changed_by)
        VALUES (TG_TABLE_NAME, 'UPDATE', NEW.employee_id, row_to_json(OLD), row_to_json(NEW), current_user);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, record_id, old_data, changed_by)
        VALUES (TG_TABLE_NAME, 'DELETE', OLD.employee_id, row_to_json(OLD), current_user);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Audit trigger on employees
CREATE TRIGGER trigger_audit_employees
    AFTER INSERT OR UPDATE OR DELETE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION audit_table_changes();

-- Trigger to validate salary
CREATE OR REPLACE FUNCTION validate_salary()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.salary < 0 THEN
        RAISE EXCEPTION 'Salary cannot be negative';
    END IF;
    IF NEW.salary > 1000000 THEN
        RAISE WARNING 'Salary exceeds typical range: %', NEW.salary;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_validate_salary
    BEFORE INSERT OR UPDATE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION validate_salary();

-- ============================================
-- 9. INSERT SAMPLE DATA
-- ============================================

-- Insert departments
INSERT INTO departments (department_name, location, budget) VALUES
('Engineering', 'San Francisco', 5000000.00),
('Sales', 'New York', 3000000.00),
('Marketing', 'Los Angeles', 2000000.00),
('HR', 'Chicago', 1000000.00),
('Finance', 'Boston', 1500000.00)
ON CONFLICT (department_name) DO NOTHING;

-- Insert employees
INSERT INTO employees (first_name, last_name, email, phone, hire_date, job_title, department_id, salary) VALUES
('John', 'Doe', 'john.doe@company.com', '555-0101', '2020-01-15', 'Senior Engineer', 1, 120000.00),
('Jane', 'Smith', 'jane.smith@company.com', '555-0102', '2019-03-20', 'Engineering Manager', 1, 150000.00),
('Bob', 'Johnson', 'bob.johnson@company.com', '555-0103', '2021-06-10', 'Sales Representative', 2, 80000.00),
('Alice', 'Williams', 'alice.williams@company.com', '555-0104', '2020-09-05', 'Sales Manager', 2, 130000.00),
('Charlie', 'Brown', 'charlie.brown@company.com', '555-0105', '2022-01-10', 'Marketing Specialist', 3, 70000.00),
('Diana', 'Davis', 'diana.davis@company.com', '555-0106', '2018-11-15', 'HR Director', 4, 140000.00),
('Edward', 'Miller', 'edward.miller@company.com', '555-0107', '2021-04-01', 'Financial Analyst', 5, 90000.00)
ON CONFLICT (email) DO NOTHING;

-- Update manager relationships
UPDATE employees SET manager_id = 2 WHERE employee_id = 1;
UPDATE employees SET manager_id = 4 WHERE employee_id = 3;
UPDATE departments SET manager_id = 2 WHERE department_id = 1;
UPDATE departments SET manager_id = 4 WHERE department_id = 2;

-- Insert projects
INSERT INTO projects (project_name, description, start_date, end_date, budget, status, department_id) VALUES
('Website Redesign', 'Complete overhaul of company website', '2024-01-01', '2024-06-30', 500000.00, 'active', 1),
('Q4 Marketing Campaign', 'Holiday season marketing push', '2024-10-01', '2024-12-31', 200000.00, 'active', 3),
('HR System Upgrade', 'Modernize HR management system', '2024-03-01', '2024-09-30', 300000.00, 'in_progress', 4),
('Sales Training Program', 'Quarterly sales training initiative', '2024-07-01', '2024-08-31', 100000.00, 'completed', 2)
ON CONFLICT DO NOTHING;

-- Insert project assignments
INSERT INTO project_assignments (employee_id, project_id, role, hours_allocated, start_date) VALUES
(1, 1, 'Lead Developer', 40.0, '2024-01-01'),
(2, 1, 'Project Manager', 20.0, '2024-01-01'),
(3, 4, 'Participant', 80.0, '2024-07-01'),
(5, 2, 'Campaign Manager', 30.0, '2024-10-01')
ON CONFLICT (employee_id, project_id) DO NOTHING;

-- Insert customers
INSERT INTO customers (company_name, contact_name, email, phone, city, country) VALUES
('Acme Corp', 'John Acme', 'contact@acme.com', '555-1001', 'New York', 'USA'),
('Tech Solutions Inc', 'Sarah Tech', 'info@techsol.com', '555-1002', 'San Francisco', 'USA'),
('Global Industries', 'Mike Global', 'sales@global.com', '555-1003', 'London', 'UK')
ON CONFLICT DO NOTHING;

-- Insert products
INSERT INTO products (product_name, category, price, stock_quantity, description) VALUES
('Laptop Pro', 'Electronics', 1299.99, 50, 'High-performance business laptop'),
('Wireless Mouse', 'Accessories', 29.99, 200, 'Ergonomic wireless mouse'),
('USB-C Cable', 'Accessories', 19.99, 500, 'Fast charging USB-C cable'),
('Monitor 27"', 'Electronics', 399.99, 30, '4K Ultra HD monitor')
ON CONFLICT DO NOTHING;

-- Insert orders
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address) VALUES
(1, '2024-11-01', 1329.98, 'completed', '123 Main St, New York, NY 10001'),
(2, '2024-11-05', 49.98, 'pending', '456 Market St, San Francisco, CA 94102'),
(3, '2024-11-10', 1419.97, 'shipped', '789 High St, London, UK')
ON CONFLICT DO NOTHING;

-- Insert order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 1299.99),
(1, 2, 1, 29.99),
(2, 2, 1, 29.99),
(2, 3, 1, 19.99),
(3, 1, 1, 1299.99),
(3, 4, 1, 119.98)
ON CONFLICT DO NOTHING;

-- Refresh materialized view
REFRESH MATERIALIZED VIEW mv_employee_stats;

-- ============================================
-- 10. GRANT PERMISSIONS (if needed)
-- ============================================

-- Example: Grant select on views
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_user;
-- GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO your_user;

-- ============================================
-- VERIFICATION QUERIES
-- ============================================

-- Check all objects created
SELECT 'Tables' AS object_type, COUNT(*) AS count FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
UNION ALL
SELECT 'Views', COUNT(*) FROM information_schema.views WHERE table_schema = 'public'
UNION ALL
SELECT 'Materialized Views', COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'VIEW' AND table_name LIKE 'mv_%'
UNION ALL
SELECT 'Indexes', COUNT(*) FROM pg_indexes WHERE schemaname = 'public'
UNION ALL
SELECT 'Functions', COUNT(*) FROM pg_proc WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
UNION ALL
SELECT 'Procedures', COUNT(*) FROM pg_proc WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public') AND prokind = 'p'
UNION ALL
SELECT 'Triggers', COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public';

