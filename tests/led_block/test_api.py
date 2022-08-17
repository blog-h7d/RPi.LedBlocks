class TestAPI:

    def test_show_blocks_returns_200(self, client):
        response = client.get('/block/')
        assert response.status_code == 200

    def test_show_block_returns_200_for_known_block(self, client):
        response = client.get('/block/default/')
        assert response.status_code == 200

    def test_show_block_returns_404_for_unknown_block(self, client):
        response = client.get('/block/unknown/')
        assert response.status_code == 404

    def test_set_program_redirects_for_known_block(self, client):
        response = client.post('/block/default/')
        assert response.status_code == 302

    def test_set_program_return_404_for_unknown_block(self, client):
        response = client.post('/block/unknown/')
        assert response.status_code == 404

    def test_get_act_colors_return_200_for_known_block(self, client):
        response = client.get('/block/default/colors/')
        assert response.status_code == 200

    def test_get_act_colors_return_404_for_unknown_block(self, client):
        response = client.get('/block/unknown/colors/')
        assert response.status_code == 404
