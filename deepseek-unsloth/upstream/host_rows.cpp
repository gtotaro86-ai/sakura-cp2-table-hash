bool llm_graph_host_rows_supported(const ggml_tensor * tab) {
    if (!tab || !tab->buffer || !tab->data || !ggml_backend_buffer_is_host(tab->buffer) || tab->view_src) {
        return false;
    }
    if (tab->nb[0] != ggml_type_size(tab->type) || tab->ne[2] != 1 || tab->ne[3] != 1) {
        return false;
    }
    return tab->type == GGML_TYPE_F32 || ggml_get_type_traits(tab->type)->to_float != nullptr;
}

void llm_graph_host_get_rows(const ggml_tensor * tab, const int32_t * ids, int64_t n_ids, float * dst) {
    const int64_t nc = tab->ne[0];
    const ggml_to_float_t to_float = tab->type == GGML_TYPE_F32 ? nullptr : ggml_get_type_traits(tab->type)->to_float;

    auto run = [&](int64_t i0, int64_t i1) {
        for (int64_t i = i0; i < i1; ++i) {
            const int64_t r = ids[i];
            GGML_ASSERT(r >= 0 && r < tab->ne[1]);
            const char * src = (const char *) tab->data + r*tab->nb[1];
            if (to_float) {
                to_float(src, dst + i*nc, nc);
            } else {
                memcpy(dst + i*nc, src, nc*sizeof(float));
            }
        }
    };

    // split prompt-sized gathers over a few threads (the CPU GET_ROWS they replace is multi-threaded)
    const int64_t n_elem = n_ids*nc;
    const int     n_thr  = (int) std::min<int64_t>(8, std::max<int64_t>(1, n_elem >> 18));
    if (n_thr <= 1) {
        run(0, n_ids);
        return;
    }
    std::vector<std::thread> workers;
    const int64_t per = (n_ids + n_thr - 1)/n_thr;
    for (int t = 1; t < n_thr; ++t) {
        const int64_t i0 = std::min<int64_t>(n_ids, t*per);
        const int64_t i1 = std::min<int64_t>(n_ids, i0 + per);
        workers.emplace_back(run, i0, i1);
    }
    run(0, std::min<int64_t>(n_ids, per));
    for (auto & w : workers) {
        w.join();
    }
}
