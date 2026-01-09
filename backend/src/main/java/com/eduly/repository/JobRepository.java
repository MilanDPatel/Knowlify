/**
 * JPA repository interface for Job entity operations.
 * 
 * Provides standard CRUD operations and query methods for managing
 * job records in the database. Extends Spring Data JPA's JpaRepository
 * for automatic implementation of common database operations.
 */
package com.eduly.repository;

import com.eduly.entity.Job;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface JobRepository extends JpaRepository<Job, String> {
}

