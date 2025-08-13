CREATE DATABASE IF NOT EXISTS cpas;
USE cpas;

-- DROP TABLE IF EXISTS team_status;
-- DROP TABLE IF EXISTS onboarding_approval;
-- DROP TABLE IF EXISTS Candidates;
-- DROP PROCEDURE IF EXISTS sp_manage_users;
-- DROP TABLE IF EXISTS Employee;

CREATE TABLE IF NOT EXISTS Employee (
    Id_user INT NOT NULL AUTO_INCREMENT,
    Username VARCHAR(100),
    Password VARCHAR(255),
    Security_key VARCHAR(250),
    Fullname VARCHAR(100),
    is_admin BOOLEAN DEFAULT 0,
    is_manager BOOLEAN DEFAULT 0,
    is_hr BOOLEAN DEFAULT 0,
    is_employee BOOLEAN DEFAULT 1,
    is_recteam BOOLEAN DEFAULT 0,
    Is_serving BOOLEAN DEFAULT 1,
    Email VARCHAR(100) UNIQUE,
    Employee_id VARCHAR(100),
    Client_name VARCHAR(100),
    Is_active BOOLEAN DEFAULT 1,
    Created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (Id_user)
) ENGINE=InnoDB;

CREATE PROCEDURE sp_manage_users (
    IN p_action VARCHAR(10),
    IN p_Id_user INT,
    IN p_Username VARCHAR(100),
    IN p_Password TEXT,
    IN p_Security_key VARCHAR(250),
    IN p_Fullname VARCHAR(100),
    IN p_is_admin BOOLEAN,
    IN p_is_manager BOOLEAN,
    IN p_is_hr BOOLEAN,
    IN p_is_employee BOOLEAN,
    IN p_is_recteam BOOLEAN,
    IN p_Is_serving BOOLEAN,
    IN p_Email VARCHAR(100),
    IN p_Employee_id VARCHAR(100),
    IN p_Client_name VARCHAR(100),
    IN p_Is_active BOOLEAN
)
BEGIN
    IF p_action = 'CREATE' THEN
        INSERT INTO Employee (
            Id_user, Username, Password, Security_key, Fullname,
            is_admin, is_manager, is_hr, is_employee, is_recteam,
            Is_serving, Email, Employee_id,
            Client_name, Is_active
        )
        VALUES (
            p_Id_user, p_Username, p_Password, p_Security_key, p_Fullname,
            p_is_admin, p_is_manager, p_is_hr, p_is_employee, p_is_recteam,
            p_Is_serving, p_Email, p_Employee_id,
            p_Client_name, p_Is_active
        );
    ELSEIF p_action = 'READ' THEN
        SELECT * FROM Employee
        WHERE (p_Id_user IS NULL OR Id_user = p_Id_user);
    ELSEIF p_action = 'UPDATE' THEN
        UPDATE Employee
        SET Username = p_Username,
            Password = p_Password,
            Security_key = p_Security_key,
            Fullname = p_Fullname,
            is_admin = p_is_admin,
            is_manager = p_is_manager,
            is_hr = p_is_hr,
            is_employee = p_is_employee,
            is_recteam = p_is_recteam,
            Is_serving = p_Is_serving,
            Email = p_Email,
            Employee_id = p_Employee_id,
            Client_name = p_Client_name,
            Is_active = p_Is_active
        WHERE Id_user = p_Id_user;
    ELSEIF p_action = 'DELETE' THEN
        DELETE FROM Employee WHERE Id_user = p_Id_user;
    END IF;
END;

INSERT INTO Employee (
    Id_user, Username, Password, Security_key, Fullname,
    is_admin, is_manager, is_hr, is_employee, is_recteam,
    Is_serving, Email, Employee_id,
    Client_name, Is_active
)
VALUES
(1, 'Alok', 'adminpass1', 'key1', 'Alok Verma', 1, 0, 0, 0, 1, 1, 'alok.verma@cpas.com', 'EMP001', 'ClientA', 1),
(2, 'Harsh', 'managerpass1', 'key2', 'Harsh Mehta', 0, 1, 0, 0, 0, 1, 'harsh.mehta@cpas.com', 'EMP002', 'ClientA', 1),
(3, 'Preeti', 'hrpass1', 'key3', 'Preeti Sharma', 0, 0, 1, 0, 1, 0, 'preeti.sharma@cpas.com', 'EMP003', 'ClientB', 1),
(4, 'Megha', 'emppass1', 'key4', 'Megha Tiwari', 0, 0, 0, 1, 1, 0, 'megha.tiwari@cpas.com', 'EMP004', 'ClientB', 1),
(5, 'Radhey', 'leadpass1', 'key5', 'Radhey Shyam', 0, 1, 1, 0, 0, 1, 'radhey.shyam@cpas.com', 'EMP005', 'ClientC', 1),
(6, 'Harshit', 'adminpass2', 'key6', 'Harshit Gupta', 1, 0, 0, 0, 0, 1, 'harshit.gupta@cpas.com', 'EMP006', 'ClientC', 1),
(7, 'Lokesh', 'managerpass2', 'key7', 'Lokesh Yadav', 0, 1, 0, 0, 1, 1, 'lokesh.yadav@cpas.com', 'EMP007', 'ClientA', 0),
(8, 'Soumya', 'emppass2', 'key8', 'Soumya Sinha', 0, 0, 0, 1, 1, 1, 'soumya.sinha@cpas.com', 'EMP008', 'ClientA', 0),
(9, 'Prateek', 'hrpass2', 'key9', 'Prateek Narang', 0, 0, 1, 0, 0, 1, 'prateek.narang@cpas.com', 'EMP009', 'ClientD', 1),
(10, 'Jitesh', 'superpass', 'key10', 'Jitesh Anand', 1, 1, 1, 1, 1, 1, 'jitesh.anand@cpas.com', 'EMP010', 'ClientD', 1);

CREATE TABLE IF NOT EXISTS Candidates (
    candidate_id INT NOT NULL PRIMARY KEY,
    candidate_name VARCHAR(255) NOT NULL,
    hr_id INT,
    total_experience FLOAT,
    resume_link VARCHAR(255),
    job_id VARCHAR(100) NOT NULL,
    manager_id INT,
    job_role VARCHAR(100),
    interview_link VARCHAR(255),
    L1_panel VARCHAR(100),
    L1_date DATETIME,
    L1_feedback VARCHAR(500),
    L1_status VARCHAR(50),
    L2_panel VARCHAR(100),
    L2_date DATETIME,
    L2_feedback VARCHAR(500),
    L2_status VARCHAR(50),
    hr_date DATETIME,
    final_feedback VARCHAR(500),
    final_comments VARCHAR(500),
    candidate_status VARCHAR(100),
    offer_letter_status TINYINT(1),
    bgv_status TINYINT(1),
    loi_status TINYINT(1),
    additional_stages INT,
    is_active TINYINT(1) DEFAULT 1,
    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_on DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_hr FOREIGN KEY (hr_id) REFERENCES Employee(Id_user),
    CONSTRAINT fk_manager FOREIGN KEY (manager_id) REFERENCES Employee(Id_user)
) ENGINE=InnoDB;

CREATE TABLE onboarding_approval (
    id INT NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    tentative_start_date DATE NOT NULL,
    shift VARCHAR(10),
    location VARCHAR(100),
    employee_personal_email VARCHAR(100) NOT NULL,
    employee_company_email VARCHAR(100),
    laptop_id VARCHAR(50),
    asset_tag VARCHAR(50),
    manager_vaco_id VARCHAR(50),
    manager_email VARCHAR(100) NOT NULL,
    project_name VARCHAR(100),
    hr_poc VARCHAR(100),
    job_title VARCHAR(100),
    teams_for_onboarding_json TEXT NOT NULL,
    approval_token VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL,
    timestamp DATETIME NOT NULL,
    approval_timestamp DATETIME,
    PRIMARY KEY (id),
    UNIQUE KEY ix_onboarding_approval_approval_token (approval_token)
);

INSERT INTO onboarding_approval (
    first_name, last_name, tentative_start_date, shift, location,
    employee_personal_email, employee_company_email,
    laptop_id, asset_tag, manager_vaco_id, manager_email,
    project_name, hr_poc, job_title,
    teams_for_onboarding_json, approval_token, status,
    timestamp, approval_timestamp
) VALUES
-- Employee 1 (Manager: Harsh)
('Ananya', 'Kapoor', '2025-08-15', 'S1', 'Mumbai',
 'ananya.kapoor@example.com', NULL,
 'LAP201', 'AST901', 'EMP002', 'harsh.mehta@cpas.com',
 'Project Sigma', 'Preeti Sharma', 'Frontend Developer',
 '["IT", "Security"]', 'tok-ananya-001', 'pending',
 NOW(), NULL),

-- Employee 2 (Manager: Radhey)
('Rohit', 'Bansal', '2025-08-20', 'S2', 'Hyderabad',
 'rohit.bansal@example.com', NULL,
 'LAP202', 'AST902', 'EMP005', 'radhey.shyam@cpas.com',
 'Project Orion', 'Prateek Narang', 'QA Analyst',
 '["QA", "Transport"]', 'tok-rohit-002', 'pending',
 NOW(), NULL),

-- Employee 3 (Manager: Jitesh)
('Simran', 'Mishra', '2025-09-01', 'S3', 'Delhi',
 'simran.mishra@example.com', NULL,
 'LAP203', 'AST903', 'EMP010', 'jitesh.anand@cpas.com',
 'Project Titan', 'Preeti Sharma', 'Backend Engineer',
 '["DevOps", "IT"]', 'tok-simran-003', 'pending',
 NOW(), NULL);


-- Table: team_status
CREATE TABLE team_status (
    id INT NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    tentative_start_date DATE NOT NULL,
    shift VARCHAR(10),
    location VARCHAR(100),
    employee_personal_email VARCHAR(100) NOT NULL,
    employee_company_email VARCHAR(100),
    laptop_id VARCHAR(50),
    asset_tag VARCHAR(50),
    manager_vaco_id VARCHAR(50),
    manager_email VARCHAR(100),
    team VARCHAR(50) NOT NULL,
    project_name VARCHAR(100),
    status VARCHAR(20),
    jira_issue_key VARCHAR(50),
    temp_id VARCHAR(50),
    onboarding_status VARCHAR(20),
    hr_poc VARCHAR(100),
    job_title VARCHAR(100),
    PRIMARY KEY (id),
    UNIQUE KEY _employee_date_team_uc (employee_personal_email, tentative_start_date, team)
);

INSERT INTO team_status (
    first_name, last_name, tentative_start_date, shift, location,
    employee_personal_email, employee_company_email,
    laptop_id, asset_tag, manager_vaco_id, manager_email,
    team, project_name, status, jira_issue_key, temp_id,
    onboarding_status, hr_poc, job_title
) VALUES
-- Ananya Kapoor (Manager: Harsh)
('Ananya', 'Kapoor', '2025-08-15', 'S1', 'Mumbai',
 'ananya.kapoor@example.com', NULL,
 'LAP201', 'AST901', 'EMP002', 'harsh.mehta@cpas.com',
 'IT', 'Project Sigma', 'pending', 'AO-101', 'TMP001',
 'initiated', 'Preeti Sharma', 'Frontend Developer'),

('Ananya', 'Kapoor', '2025-08-15', 'S1', 'Mumbai',
 'ananya.kapoor@example.com', NULL,
 'LAP201', 'AST901', 'EMP002', 'harsh.mehta@cpas.com',
 'Security', 'Project Sigma', 'pending', 'AO-102', 'TMP001',
 'initiated', 'Preeti Sharma', 'Frontend Developer'),

-- Rohit Bansal (Manager: Radhey)
('Rohit', 'Bansal', '2025-08-20', 'S2', 'Hyderabad',
 'rohit.bansal@example.com', NULL,
 'LAP202', 'AST902', 'EMP005', 'radhey.shyam@cpas.com',
 'QA', 'Project Orion', 'pending', 'AO-103', 'TMP002',
 'initiated', 'Prateek Narang', 'QA Analyst'),

('Rohit', 'Bansal', '2025-08-20', 'S2', 'Hyderabad',
 'rohit.bansal@example.com', NULL,
 'LAP202', 'AST902', 'EMP005', 'radhey.shyam@cpas.com',
 'Transport', 'Project Orion', 'pending', 'AO-104', 'TMP002',
 'initiated', 'Prateek Narang', 'QA Analyst'),

-- Simran Mishra (Manager: Jitesh)
('Simran', 'Mishra', '2025-09-01', 'S3', 'Delhi',
 'simran.mishra@example.com', NULL,
 'LAP203', 'AST903', 'EMP010', 'jitesh.anand@cpas.com',
 'DevOps', 'Project Titan', 'pending', 'AO-105', 'TMP003',
 'initiated', 'Preeti Sharma', 'Backend Engineer'),

('Simran', 'Mishra', '2025-09-01', 'S3', 'Delhi',
 'simran.mishra@example.com', NULL,
 'LAP203', 'AST903', 'EMP010', 'jitesh.anand@cpas.com',
 'IT', 'Project Titan', 'pending', 'AO-106', 'TMP003',
 'initiated', 'Preeti Sharma', 'Backend Engineer');

