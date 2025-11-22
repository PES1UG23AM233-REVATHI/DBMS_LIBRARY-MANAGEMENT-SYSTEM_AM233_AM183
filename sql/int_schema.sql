USE library_management_db;

DROP PROCEDURE IF EXISTS ProcessReturn;
DROP PROCEDURE IF EXISTS CalculatePenalty;

DELIMITER $$

CREATE PROCEDURE CalculatePenalty(
    IN p_issue_id VARCHAR(10),
    IN p_return_date DATE,
    OUT p_penalty_amount DECIMAL(10,2)
)
BEGIN
    DECLARE v_due_date DATE;
    DECLARE v_days_overdue INT;
    DECLARE v_first_week_days INT;
    DECLARE v_remaining_days INT;

    -- Get due date for the issue
    SELECT due_date INTO v_due_date
    FROM issues
    WHERE id = p_issue_id
    LIMIT 1;

    -- If input is invalid, just set penalty to 0
    IF p_return_date IS NULL OR v_due_date IS NULL THEN
        SET p_penalty_amount = 0.00;
    ELSE
        IF p_return_date > v_due_date THEN
            SET v_days_overdue = DATEDIFF(p_return_date, v_due_date);

            IF v_days_overdue <= 7 THEN
                SET v_first_week_days = v_days_overdue;
                SET v_remaining_days = 0;
            ELSE
                SET v_first_week_days = 7;
                SET v_remaining_days = v_days_overdue - 7;
            END IF;

            -- First week ₹1/day, after first week ₹2/day
            SET p_penalty_amount = (v_first_week_days * 1.0) + (v_remaining_days * 2.0);
        ELSE
            SET p_penalty_amount = 0.00;
        END IF;
    END IF;
END$$

-- ProcessReturn procedure
CREATE PROCEDURE ProcessReturn(
    IN p_issue_id VARCHAR(10),
    IN p_return_date DATE,
    IN p_condition_notes VARCHAR(255)
)
BEGIN
    DECLARE v_penalty_amount DECIMAL(10,2);

    -- Calculate penalty using OUT parameter
    CALL CalculatePenalty(p_issue_id, p_return_date, @out_penalty);
    SELECT @out_penalty INTO v_penalty_amount;

    -- Insert return record if not already returned
    IF NOT EXISTS (SELECT 1 FROM returns WHERE issue_id = p_issue_id) THEN
        INSERT INTO returns (issue_id, return_date, condition_notes)
        VALUES (p_issue_id, p_return_date, p_condition_notes);
    END IF;

    -- Update penalty in issues table
    UPDATE issues
    SET penalty_amount = v_penalty_amount
    WHERE id = p_issue_id;

END$$

DELIMITER ;
