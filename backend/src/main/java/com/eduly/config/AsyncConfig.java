/**
 * Configuration class for asynchronous task execution.
 * 
 * Configures a thread pool executor for running job processing tasks
 * asynchronously. This allows the API to respond immediately to job
 * start requests while processing happens in the background.
 * 
 * Thread pool settings: 2-5 threads, queue capacity of 100.
 */
package com.eduly.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;

@Configuration
@EnableAsync
public class AsyncConfig {
    @Bean(name = "taskExecutor")
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(2);
        executor.setMaxPoolSize(5);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("job-processing-");
        executor.initialize();
        return executor;
    }
}

